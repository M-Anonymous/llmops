import asyncio

from fastapi import UploadFile


class FileService:



    async def download_file(self):
        pass


    @classmethod
    def stream_upload_file(cls,file: UploadFile, chunk_size: int = 1024 * 1024):
        """
        同步流式读取上传文件（专为 COS SDK 设计）
        """
        # 获取当前事件循环，用于在同步代码中调用异步方法
        loop = asyncio.get_event_loop()

        while True:
            # 将异步的 file.read() 放入线程池执行，并阻塞等待结果
            # 这样既不会阻塞 FastAPI 的事件循环，又能生成同步的数据块
            future = asyncio.run_coroutine_threadsafe(file.read(chunk_size), loop)
            chunk = future.result()  # 同步获取读取到的数据

            # 如果读到空字节，说明文件已读完，退出循环
            if not chunk:
                break

            yield chunk  # 同步生成器，COS SDK 可以正常消费