import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8000/audiorequester'

export const searchVideos = async (query) => {
  const response = await axios.get(`${API_BASE_URL}/search`, {
    params: { query },
  })
  return response.data
}

export const downloadVideo = async (videoId) => {
  const response = await axios.get(`${API_BASE_URL}/download`, {
    params: { video_id: videoId },
    responseType: 'blob',
  })
  return response.data
}
