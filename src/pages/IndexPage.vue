<template>
  <q-layout>
    <div class="row justify-center">
      <div>
        <q-img class="flex"
          alt="Audio Toolkit logo"
          src="../assets/logoLessBorders.png"
          spinner-color="white"
          style="width: 160px; height: 160px;"
        />
      </div>
    </div>
    <q-page-container>
      <q-page class="flex flex-center">
        <div class="container">
          <SearchBar @video-selected="selectVideo" />
          <VideoList :video="selectedVideo" />
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script>
  import SearchBar from "../components/SearchBar.vue";
  import VideoList from "../components/VideoList.vue";

  export default {
    name: "HomeView",
    components: { SearchBar, VideoList },
    data() {
      return {
        selectedVideo: null,
      };
    },
    methods: {
      selectVideo(video) {
        this.selectedVideo = video;
      },
    },
  };
</script>
