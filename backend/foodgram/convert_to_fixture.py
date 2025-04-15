import json

with open('ingredients.json', 'r', encoding='utf-8') as f:
    input_data = json.load(f)

output_data = [
    {
        "model": "recipes.ingredient",
        "pk": i+1,  # Автонумерация начиная с 1
        "fields": item
    }
    for i, item in enumerate(input_data)
]

with open('ingredients_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("Файл успешно преобразован и сохранён как ingredients_fixed.json")