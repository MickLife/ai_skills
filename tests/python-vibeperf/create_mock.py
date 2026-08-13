import json
import os

# 创建一个 mock 的 viztracer json 数据
mock_data = {
    'traceEvents': [
        {'ph': 'X', 'name': 'my_module.slow_function', 'dur': 5000000}, # 5s
        {'ph': 'X', 'name': 'my_module.slow_function', 'dur': 5000000}, # 5s
        {'ph': 'X', 'name': 'other_module.fast_function', 'dur': 1500}, # 1.5ms
        {'ph': 'X', 'name': 'other_module.fast_function', 'dur': 1200}, # 1.2ms
        {'ph': 'X', 'name': 'main', 'dur': 10002700} # 10s
    ]
}

os.makedirs('data', exist_ok=True)
with open('data/mock_viz.json', 'w') as f:
    json.dump(mock_data, f)
print("Mock data created at data/mock_viz.json")
