<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const category = ref(route.params.category as string);
const photos = ref<{ id: number; path: string }[]>([]);

const loadPhotos = async () => {
  try {
    const response = await fetch(`http://localhost:3000/api/images/${category.value}`);
    const data = await response.json();
    photos.value = data;
  } catch (error) {
    console.error('Erreur lors du chargement des images:', error);
  }
};

watch(() => route.params.category, (newCategory) => {
  category.value = newCategory as string;
  loadPhotos();
});

onMounted(() => {
  loadPhotos();
});
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold text-center mb-12 capitalize text-white">{{ category }}</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      <div v-for="photo in photos" :key="photo.id" class="gallery-item aspect-square">
        <img :src="'http://localhost:3000' + photo.path" :alt="'Photo ' + photo.id" class="w-full h-full object-cover">
      </div>
    </div>
  </div>
</template>