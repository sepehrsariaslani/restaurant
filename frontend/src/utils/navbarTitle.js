// استور ساده عنوان navbar — صفحات می‌توانند عنوان خود را به هدر مدیریت بفرستند
import { ref } from "vue";

export const navbarTitle = ref("");

export function setNavbarTitle(title) {
  navbarTitle.value = String(title || "").trim();
}

export function clearNavbarTitle() {
  navbarTitle.value = "";
}
