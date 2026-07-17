import glob
import re

files = glob.glob("frontend/src/pages/management/ManagementOrdersPage.vue")

for file in files:
    with open(file, "r") as f:
        content = f.read()
        
    t_open = content.count("<template>")
    t_if_open = content.count("<template v-if=")
    t_else_open = content.count("<template v-else")
    t_total_open = t_open + t_if_open + t_else_open
    t_close = content.count("</template>")
    
    if t_total_open != t_close:
        print(f"Error in {file}:")
        print(f"  Template Open: {t_total_open} ({t_open} + {t_if_open} + {t_else_open}) vs Close: {t_close}")
        
print("Syntax check finished.")
