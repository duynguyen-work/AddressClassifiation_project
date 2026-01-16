import json

test_path = "test_5"
# Các file output
# Đường dẫn file json gốc
file_json = test_path +  f"/{test_path}.json"
province_file = test_path + "/list_province.txt"
district_file = test_path +"/list_district.txt"
ward_file = test_path + "/list_ward.txt"

with open(file_json, encoding='utf-8') as f:
    data = json.load(f)

provinces, districts, wards = [], [], []

for test_idx, data_point in enumerate(data):
    answer = data_point["result"]
    provinces.append(answer["province"])
    districts.append(answer["district"])
    wards.append(answer["ward"])

# Ghi ra file
with open(province_file, "w", encoding="utf-8") as f:
    f.write("\n".join(provinces))

with open(district_file, "w", encoding="utf-8") as f:
    f.write("\n".join(districts))

with open(ward_file, "w", encoding="utf-8") as f:
    f.write("\n".join(wards))

print("Đã tạo xong 3 file:", province_file, district_file, ward_file)
