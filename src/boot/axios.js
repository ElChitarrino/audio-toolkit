//import { defineBoot } from '#q-app/wrappers'
import axios from 'axios'

// Be careful when using SSR for cross-request state pollution
// due to creating a Singleton instance here;
// If any client changes this (global) instance, it might be a
// good idea to move this instance creation inside of the
// "export default () => {}" function below (which runs individually
// for each client)
const API_BASE_URL = 'http://127.0.0.1:8000/audiorequester';
//const api = axios.create({ baseURL: 'http://127.0.0.1:8000/audiorequester' });


// export default defineBoot(({ app }) => {
//   // for use inside Vue files (Options API) through this.$axios and this.$api

//   app.config.globalProperties.$axios = axios
//   // ^ ^ ^ this will allow you to use this.$axios (for Vue Options API form)
//   //       so you won't necessarily have to import axios in each vue file

//   app.config.globalProperties.$api = api
//   // ^ ^ ^ this will allow you to use this.$api (for Vue Options API form)
//   //       so you can easily perform requests against your app's API
// })

export const searchVideos = async (query) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/search`, {
      params: { query },
    });
    return response?.data; // Assuming the API returns a list of videos
  } catch (error) {
    console.error(error.message);
  }
};

export const downloadVideo = async (videoId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/download`, {
      params: { video_id: videoId },
    });
    return response.data; // Assuming the API confirms the download
  } catch (error) {
    console.error(error.message);
  }
};

//export { api }
