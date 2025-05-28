<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isMenuOpen = ref(false)

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}
</script>

<template>
  <div class="min-h-screen bg-black">
    <nav class="bg-gray-900 shadow-lg">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex justify-between h-16">
          <div class="flex">
            <router-link to="/" class="flex items-center">
              <span class="text-xl font-bold text-white">Sports Portfolio</span>
            </router-link>
          </div>

          <!-- Desktop Menu -->
          <div class="hidden md:flex items-center space-x-4">
            <router-link to="/gallery/football" class="text-gray-300 hover:text-white">Football</router-link>
            <router-link to="/gallery/basketball" class="text-gray-300 hover:text-white">Basketball</router-link>
            <router-link to="/gallery/handball" class="text-gray-300 hover:text-white">Handball</router-link>
            <router-link to="/gallery/boxing" class="text-gray-300 hover:text-white">Boxe</router-link>
            <router-link to="/about" class="text-gray-300 hover:text-white">À propos</router-link>
            <router-link to="/contact" class="text-gray-300 hover:text-white">Contact</router-link>
          </div>

          <!-- Mobile Menu Button -->
          <div class="md:hidden flex items-center">
            <button @click="toggleMenu" class="text-gray-300 hover:text-white">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path v-if="!isMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile Menu -->
      <div v-if="isMenuOpen" class="md:hidden bg-gray-900">
        <div class="px-2 pt-2 pb-3 space-y-1">
          <router-link @click="toggleMenu" to="/gallery/football" class="block px-3 py-2 text-gray-300 hover:text-white">Football</router-link>
          <router-link @click="toggleMenu" to="/gallery/basketball" class="block px-3 py-2 text-gray-300 hover:text-white">Basketball</router-link>
          <router-link @click="toggleMenu" to="/gallery/handball" class="block px-3 py-2 text-gray-300 hover:text-white">Handball</router-link>
          <router-link @click="toggleMenu" to="/gallery/boxing" class="block px-3 py-2 text-gray-300 hover:text-white">Boxe</router-link>
          <router-link @click="toggleMenu" to="/about" class="block px-3 py-2 text-gray-300 hover:text-white">À propos</router-link>
          <router-link @click="toggleMenu" to="/contact" class="block px-3 py-2 text-gray-300 hover:text-white">Contact</router-link>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 py-8">
      <router-view></router-view>
    </main>
  </div>
</template>