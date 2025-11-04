import "python:MathExpressionGenerator" as generator

module MathExpressionGenerator:
    def generate_expression(language: String, max_depth: Int = 3) -> String:
        python_generator = generator.MathExpressionGenerator(["c.bnf", "python.bnf", "ruby.bnf", "javascript.bnf"])
        return python_generator.generate_expression(language, max_depth)

# 使用例
language = "python"
expression = MathExpressionGenerator.generate_expression(language)
print(f"Generated expression in {language}: {expression}")
