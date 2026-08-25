<template>
  <svg
    class="management-bear-logo"
    viewBox="0 0 64 64"
    aria-hidden="true"
    focusable="false"
  >
    <g class="logo-stroke">
      <path
        class="head-outline"
        d="M32 11.8c-3.7 0-7.1 1.1-9.8 3.1c-3.7 2.7-6.1 6.7-6.8 11.3
           c-.8 5.4.3 10.1 3 13.9c2.7 3.9 6.6 6.4 11.3 7.4
           c1.5.3 3.1.3 4.6 0c4.7-1 8.6-3.5 11.3-7.4c2.7-3.8 3.8-8.5 3-13.9
           c-.7-4.6-3.1-8.6-6.8-11.3c-2.7-2-6.1-3.1-9.8-3.1Z"
      />

      <path
        class="ear-outline"
        d="M20.5 16.7c-2.6 0-4.7-2.1-4.7-4.7s2.1-4.7 4.7-4.7s4.7 2.1 4.7 4.7s-2.1 4.7-4.7 4.7Z"
      />
      <path
        class="ear-outline"
        d="M43.5 16.7c2.6 0 4.7-2.1 4.7-4.7s-2.1-4.7-4.7-4.7s-4.7 2.1-4.7 4.7s2.1 4.7 4.7 4.7Z"
      />
      <path
        class="ear-inner"
        d="M20.5 14.1c-1.2 0-2.2-1-2.2-2.2s1-2.2 2.2-2.2s2.2 1 2.2 2.2s-1 2.2-2.2 2.2Z"
      />
      <path
        class="ear-inner"
        d="M43.5 14.1c1.2 0 2.2-1 2.2-2.2s-1-2.2-2.2-2.2s-2.2 1-2.2 2.2s1 2.2 2.2 2.2Z"
      />

      <path class="brow-line" d="M25.5 25.1c1-.8 2.2-1.3 3.5-1.3" />
      <path class="brow-line" d="M38.5 25.1c-1-.8-2.2-1.3-3.5-1.3" />
      <path class="eye-line" d="M26.6 27.4h2.1" />
      <path class="eye-line" d="M35.3 27.4h2.1" />

      <ellipse class="muzzle-line" cx="32" cy="29.5" rx="5.6" ry="4.1" />
      <path class="nose-line" d="M32 27.2l2.2 1.8h-4.4z" />
      <path class="nose-line" d="M32 29.1v2.3" />
      <path class="snout-line" d="M29.9 31.8c.7.8 1.4 1.2 2.1 1.2s1.4-.4 2.1-1.2" />

      <path class="jaw-line" d="M23.2 34.5c1.1 2 2.7 3.5 4.8 4.4" />
      <path class="jaw-line" d="M40.8 34.5c-1.1 2-2.7 3.5-4.8 4.4" />
    </g>
  </svg>
</template>

<style scoped>
.management-bear-logo {
  display: block;
  width: 100%;
  height: 100%;
}

.logo-stroke {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.head-outline {
  stroke-width: 2.45;
}

.ear-outline {
  stroke-width: 2.05;
}

.ear-inner,
.muzzle-line,
.brow-line,
.eye-line {
  stroke-width: 1.5;
  opacity: 0.9;
}

.nose-line,
.snout-line,
.jaw-line {
  stroke-width: 1.35;
  opacity: 0.86;
}
</style>
