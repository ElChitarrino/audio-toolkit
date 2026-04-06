import axios from 'axios'

const API = '/audiorequester'

export const searchVideos = async (query) => {
  const response = await axios.get(`${API}/search`, { params: { query } })
  return response.data
}

export const downloadVideo = async (videoId) => {
  const response = await axios.get(`${API}/download`, {
    params: { video_id: videoId },
    responseType: 'blob',
  })
  return response.data
}

export const getLibrary = async () => {
  const response = await axios.get(`${API}/library`)
  return response.data
}

export const deleteTrack = async (videoId) => {
  const response = await axios.delete(`${API}/library/${videoId}`)
  return response.data
}

export const getAudioUrl = (videoId) => `${API}/audio/${videoId}`
