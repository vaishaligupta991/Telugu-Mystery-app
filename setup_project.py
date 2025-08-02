import os

directories = [
    ".streamlit",
    "database",
    "components",
    "pages",
    "assets/styles",
    "assets/images/cultural_patterns",
    "assets/fonts",
    "data/database",
    "data/audio",
    "data/images",
    "data/exports",
    "data/backups",
    "utils",
    "tests"
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"✅ Created: {directory}")
    if directory in ["database", "components", "pages", "utils", "tests"]:
        with open(os.path.join(directory, "__init__.py"), "w") as f:
            f.write("# Package initialization\n")

print("\n🎉 Project structure created successfully!")
