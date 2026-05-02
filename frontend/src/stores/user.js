/**
 * 用户状态管理
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import request from "../utils/request";

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "");
  const user = ref(JSON.parse(localStorage.getItem("user") || "{}"));

  const isLoggedIn = computed(() => !!token.value);
  const isAdmin = computed(() => user.value.is_admin === true);
  const username = computed(() => user.value.username || "");

  async function login(username, password) {
    const res = await request.post("/auth/login", { username, password });
    token.value = res.access_token;
    localStorage.setItem("token", res.access_token);
    await fetchUser();
    return res;
  }

  async function fetchUser() {
    try {
      const res = await request.get("/auth/me");
      user.value = res;
      localStorage.setItem("user", JSON.stringify(res));
    } catch {
      logout();
    }
  }

  function logout() {
    token.value = "";
    user.value = {};
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  }

  return { token, user, isLoggedIn, isAdmin, username, login, fetchUser, logout };
});
