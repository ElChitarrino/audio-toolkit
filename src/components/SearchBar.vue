<template>
  <div>
    <h4 class="text-h4">Video Search on Youtube</h4>
    <q-input rounded outlined
      v-model="query"
      placeholder="Search for videos..."
      class="search-bar"
      @update:model-value="onInput"
    />
    <ul
      v-if="suggestions.length"
      class="suggestions"
    >
      <li
        v-for="video in suggestions"
        :key="video.id"
        @click="onSelect(video)"
      >
        <img
          :src="video.thumbnail"
          alt="Thumbnail"
        >
        <span>{{ video.title }}</span>
      </li>
    </ul>
  </div>
</template>

<script>
  import { searchVideos } from "../boot/axios";

  export default {
    name: "SearchBar",
    emits: ["video-selected"],
    data() {
      return {
        query: "",
        suggestions: [],
      };
    },
    methods: {
      async onInput() {
        if (this.query.length > 2) {
          this.suggestions = await searchVideos(this.query);
        } else {
          this.suggestions = [];
        }
      },
      onSelect(video) {
        this.$emit("video-selected", video);
        this.query = video.title; // Optionally set the query to the selected title
        this.suggestions = []; // Clear suggestions
      },
    },
  };
</script>

<style>
  .search-bar {
    width: 100%;
    padding: 10px;
  }
  .suggestions {
    list-style: none;
  margin: 0;
  padding: 0;
  }
  .suggestions li {
    display: flex;
    align-items: center;
    cursor: pointer;
  }
  .suggestions li img {
    width: 50px;
    height: 50px;
    margin-right: 10px;
  }
</style>
