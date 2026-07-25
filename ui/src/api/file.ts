import { apiRequest } from './client'

export interface PresignedUploadResult {
  upload_url: string
  cos_key: string
  filename: string
  content_type: string
  expire_seconds: number
}

export interface PresignedUploadInput {
  filename: string
  extension: string
  folder?: string
}

export function getPresignedUploadUrl(data: PresignedUploadInput) {
  return apiRequest<PresignedUploadResult>('/file/presigned_upload', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function uploadFileToCos(file: File, folder = 'uploads') {
  const dotIndex = file.name.lastIndexOf('.')
  const hasExtension = dotIndex > 0
  const filename = hasExtension ? file.name.slice(0, dotIndex) : file.name
  const extension = hasExtension ? file.name.slice(dotIndex + 1) : 'txt'

  const presigned = await getPresignedUploadUrl({ filename, extension, folder })

  const uploadResponse = await fetch(presigned.upload_url, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': presigned.content_type },
  })

  if (!uploadResponse.ok) {
    throw new Error('文件上传到 COS 失败')
  }

  return {
    cos_key: presigned.cos_key,
    file_name: filename,
    file_ext: extension,
    filename: presigned.filename,
  }
}
