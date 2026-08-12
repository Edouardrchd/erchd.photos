<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { CATEGORIES, labelFor, photosFor } from '../photos';

const route = useRoute();

const category = computed(() => String(route.params.category ?? ''));
const isKnown = computed(() => CATEGORIES.some((c) => c.slug === category.value));
const title = computed(() => labelFor(category.value));
const photos = computed(() => photosFor(category.value));
</script>

<template>
  <div>
    <h1 class="text-4xl font-bold text-center mb-12 capitalize text-white">{{ title }}</h1>

    <div v-if="photos.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      <div v-for="photo in photos" :key="photo.id" class="gallery-item aspect-square">
        <img :src="photo.src" :alt="photo.alt" loading="lazy" decoding="async" class="w-full h-full object-cover">
      </div>
    </div>

    <p v-else-if="isKnown" class="text-center text-gray-400">
      Aucune photo pour le moment.
      <br>
      Depose des images dans <code class="text-gray-200">project/src/assets/photos/{{ category }}/</code> pour les voir apparaitre ici.
    </p>

    <p v-else class="text-center text-gray-400">
      Cette galerie n'existe pas.
      <router-link to="/" class="underline hover:text-white">Retour a l'accueil</router-link>
    </p>
  </div>
</template>
