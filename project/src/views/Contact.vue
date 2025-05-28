<script setup lang="ts">
import { ref } from 'vue';

const name = ref('');
const email = ref('');
const userMessage = ref('');
const message = ref('');
const isSuccess = ref(false);
const isError = ref(false);

const handleSubmit = async () => {
  try {
    const response = await fetch('http://localhost:3000/api/contact', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: name.value,
        email: email.value,
        message: userMessage.value
      }),
    });

    if (response.ok) {
      isSuccess.value = true;
      message.value = 'Message envoyé avec succès !';
      name.value = '';
      email.value = '';
      userMessage.value = '';
    } else {
      throw new Error('Erreur lors de l\'envoi du message');
    }
  } catch (error) {
    isError.value = true;
    message.value = 'Une erreur est survenue. Veuillez réessayer.';
  }
};
</script>

<style scoped>
.card {
  width: 240px;
  height: 254px;
  padding: 0 15px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  background: #1a1a1a;
  border-radius: 20px;
}

.card > * {
  margin: 0;
}

.card__title {
  font-size: 23px;
  font-weight: 900;
  color: #ffffff;
}

.card__content {
  font-size: 13px;
  line-height: 18px;
  color: #cccccc;
}

.card__form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card__form input, .card__form textarea {
  margin-top: 10px;
  outline: 0;
  background: rgb(26, 26, 26);
  box-shadow: transparent 0px 0px 0px 1px inset;
  padding: 0.6em;
  border-radius: 14px;
  border: 1px solid #333;
  color: white;
}

.card__form button {
  border: 0;
  background: #333;
  color: #fff;
  padding: 0.68em;
  border-radius: 14px;
  font-weight: bold;
}

.sign-up:hover {
  opacity: 0.8;
}

.message {
  margin-top: 1rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
}

.success {
  background-color: #064e3b;
  color: white;
}

.error {
  background-color: #7f1d1d;
  color: white;
}
</style>

<template>
  <div class="flex justify-center items-center min-h-[80vh]">
    <div class="card">
      <span class="card__title">Contact</span>
      <p class="card__content">Envoyez-nous un message</p>
      <form class="card__form" @submit.prevent="handleSubmit">
        <input 
          v-model="name"
          placeholder="Votre nom" 
          type="text"
          required
        >
        <input 
          v-model="email"
          placeholder="Votre email" 
          type="email"
          required
        >
        <textarea 
          v-model="userMessage"
          placeholder="Votre message"
          required
          rows="3"
        ></textarea>
        <button type="submit" class="sign-up">Envoyer</button>
      </form>
      <div v-if="message" :class="['message', isSuccess ? 'success' : 'error']">
        {{ message }}
      </div>
    </div>
  </div>
</template>