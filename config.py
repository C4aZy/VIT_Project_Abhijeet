# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./code_review.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    # ML Models
    MODEL_PATH: str = "./models/"
    HUGGINGFACE_CACHE: str = "./models/huggingface/"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Code Review Assistant"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    
    # Analysis Settings
    MAX_COMPLEXITY_THRESHOLD: int = 10
    MIN_CODE_QUALITY_SCORE: float = 7.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


# backend/app/analyzers/ast_parser.py
import ast
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FunctionInfo:
    name: str
    line_number: int
    args: List[str]
    returns: Optional[str]
    complexity: int
    lines_of_code: int
    has_docstring: bool
    docstring: Optional[str]
    calls: List[str]

@dataclass
class ClassInfo:
    name: str
    line_number: int
    methods: List[FunctionInfo]
    bases: List[str]
    has_docstring: bool
    docstring: Optional[str]

@dataclass
class ASTAnalysisResult:
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[str]
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    complexity_score: int

class ASTParser:
    """Parse Python code using AST and extract structural information"""
    
    def __init__(self):
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.imports: List[str] = []
        self.total_complexity = 0
    
    def parse_file(self, file_path: str) -> Optional[ASTAnalysisResult]:
        """Parse a Python file and extract information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            return self.parse_code(source_code)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None
    
    def parse_code(self, source_code: str) -> ASTAnalysisResult:
        """Parse Python source code"""
        try:
            tree = ast.parse(source_code)
            self._analyze_tree(tree)
            
            # Count lines
            lines = source_code.split('\n')
            total_lines = len(lines)
            blank_lines = sum(1 for line in lines if not line.strip())
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            code_lines = total_lines - blank_lines - comment_lines
            
            return ASTAnalysisResult(
                functions=self.functions,
                classes=self.classes,
                imports=self.imports,
                total_lines=total_lines,
                code_lines=code_lines,
                comment_lines=comment_lines,
                blank_lines=blank_lines,
                complexity_score=self.total_complexity
            )
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            raise
    
    def _analyze_tree(self, tree: ast.AST):
        """Recursively analyze AST tree"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node)
            elif isinstance(node, ast.ClassDef):
                self._analyze_class(node)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._analyze_import(node)
    
    def _analyze_function(self, node: ast.FunctionDef) -> FunctionInfo:
        """Analyze a function definition"""
        # Extract arguments
        args = [arg.arg for arg in node.args.args]
        
        # Get return type annotation
        returns = None
        if node.returns:
            returns = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
        
        # Check for docstring
        docstring = ast.get_docstring(node)
        has_docstring = docstring is not None
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        self.total_complexity += complexity
        
        # Count lines of code
        lines_of_code = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
        
        # Find function calls
        calls = self._find_function_calls(node)
        
        func_info = FunctionInfo(
            name=node.name,
            line_number=node.lineno,
            args=args,
            returns=returns,
            complexity=complexity,
            lines_of_code=lines_of_code,
            has_docstring=has_docstring,
            docstring=docstring,
            calls=calls
        )
        
        self.functions.append(func_info)
        return func_info
    
    def _analyze_class(self, node: ast.ClassDef):
        """Analyze a class definition"""
        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
        
        # Get docstring
        docstring = ast.get_docstring(node)
        has_docstring = docstring is not None
        
        # Analyze methods
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._analyze_function(item)
                methods.append(method_info)
        
        class_info = ClassInfo(
            name=node.name,
            line_number=node.lineno,
            methods=methods,
            bases=bases,
            has_docstring=has_docstring,
            docstring=docstring
        )
        
        self.classes.append(class_info)
    
    def _analyze_import(self, node: ast.AST):
        """Analyze import statements"""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                self.imports.append(f"{module}.{alias.name}")
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.Break, ast.Continue)):
                complexity += 1
        
        return complexity
    
    def _find_function_calls(self, node: ast.AST) -> List[str]:
        """Find all function calls within a node"""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return list(set(calls))  # Remove duplicates
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the analysis"""
        return {
            "total_functions": len(self.functions),
            "total_classes": len(self.classes),
            "total_imports": len(self.imports),
            "average_complexity": self.total_complexity / len(self.functions) if self.functions else 0,
            "max_complexity": max((f.complexity for f in self.functions), default=0),
            "functions_without_docstrings": sum(1 for f in self.functions if not f.has_docstring),
            "classes_without_docstrings": sum(1 for c in self.classes if not c.has_docstring)
        }


# Example usage and testing
if __name__ == "__main__":
    # Test code
    test_code = '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers"""
    if a > 0 and b > 0:
        return a + b
    elif a < 0 or b < 0:
        return 0
    return a + b

class Calculator:
    """A simple calculator class"""
    
    def add(self, x, y):
        return x + y
    
    def subtract(self, x, y):
        # This function has no docstring
        if x > y:
            return x - y
        else:
            return y - x
'''
    
    parser = ASTParser()
    result = parser.parse_code(test_code)
    
    print("Functions:", [f.name for f in result.functions])
    print("Classes:", [c.name for c in result.classes])
    print("Total Complexity:", result.complexity_score)
    print("\nSummary:", parser.get_summary())