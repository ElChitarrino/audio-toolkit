<template>
  <div>
    <q-separator id="videoListSeparator" color="dark grey" inset/>
    <p class="text-body1 text-center text-bold">Selected Video:</p>
    <div
      v-if="video"
    >
      <q-img
        :src="video.thumbnail"
        alt="Thumbnail"
      />
      <p class="text-body1 text-center">{{ video.title }}</p>
      <button @click="download(video.videoId)">
        Download
      </button>
    </div>
  </div>
</template>

<script>
  import { downloadVideo } from "../boot/axios";

  export default {
    name: "VideoList",
    props: {
      video: {
        type: Object, // Specify the type of the prop (String, Number, Object, Array, etc.)
        required: true, // Optional: Enforce that the prop must be passed
        // default: () => ({}), // Optional: Provide a default value
      },
    },
    methods: {
      async download(videoId) {
        console.log("Test Download of " + videoId);
        await downloadVideo(videoId);
        alert("Download started!");
      },
    }
  };
</script>

<style>
  #videoListSeparator {
    margin-top: 40px;
    margin-bottom: 20px;
  }
  .text-body1 {
    font-size: 16px;
  }
  .text-center {
    text-align: center;
  }
  .text-bold {
    font-weight: bold;
  }
</style>
