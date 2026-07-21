def get_file_type_from_url(url: str) -> str | None:
    """从预签名 URL 中提取文件类型"""
    # 1. 先去掉 ? 后面的所有查询参数
    path_part = url.split('?')[0]
    # 2. 再从路径中提取文件名和扩展名
    file_name = path_part.split('/')[-1]
    if '.' in file_name:
        return file_name.split('.')[-1]  # 返回如 'pdf', 'txt'
    return None


type = get_file_type_from_url("https://llmops-1258847722.cos.ap-chongqing.myqcloud.com/uploads/afc71cc285e7420e9077b0184bbae80b_test.txt?q-sign-algorithm=sha1&q-ak=AKID0RvLyUvCIMc8Vp6GLKDxbCdx87uVu6A4&q-sign-time=1784625524%3B1784625884&q-key-time=1784625524%3B1784625884&q-header-list=host&q-url-param-list=&q-signature=f58c934ab399c9b4ab61b0e3a9ea8e549b9213b0")
print(type)