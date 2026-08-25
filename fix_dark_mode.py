with open('frontend/src/App.vue', 'r') as f:
    content = f.read()

old_dark = """:root.dark,
body.management-theme-dark {
  --mg-bg-page: #1C1512;
  --mg-bg-surface: #261D18;
  --mg-bg-soft: #30241E;
  --mg-text-main: #F4EFE6;
  --mg-text-muted: #BFA78E;
  --mg-border: #4D3B31;
  --mg-border-light: rgba(77, 59, 49, 0.5);
  --mg-primary: #B26A4A;
  --mg-primary-hover: #C97852;
  --mg-olive: #797855;
  --mg-olive-soft: #3D3C2A;
  --mg-danger: #C2564C;
  --mg-danger-bg: #4D2B24;
  --mg-success: #88935C;
  --mg-success-bg: #3A4027;
  --mg-shadow-sm: 0 8px 24px rgba(0, 0, 0, 0.3);
  --mg-shadow-md: 0 18px 40px rgba(0, 0, 0, 0.5);
}"""

new_dark = """:root.dark,
body.management-theme-dark {
  --mg-bg-page: #1C1A18;
  --mg-bg-surface: #25221F;
  --mg-bg-soft: #2E2A27;
  --mg-text-main: #EAE5DF;
  --mg-text-muted: #A39B93;
  --mg-border: #423C38;
  --mg-border-light: rgba(66, 60, 56, 0.5);
  --mg-primary: #C07050;
  --mg-primary-hover: #D4805E;
  --mg-olive: #838561;
  --mg-olive-soft: #303225;
  --mg-danger: #C25B4E;
  --mg-danger-bg: #3D231E;
  --mg-success: #7F8B54;
  --mg-success-bg: #2E3321;
  --mg-shadow-sm: 0 8px 24px rgba(0, 0, 0, 0.4);
  --mg-shadow-md: 0 18px 40px rgba(0, 0, 0, 0.6);
}"""

content = content.replace(old_dark, new_dark)

with open('frontend/src/App.vue', 'w') as f:
    f.write(content)
