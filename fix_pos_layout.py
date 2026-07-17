with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

content = content.replace(
    '''	width: 100%;
	height: 100vh;
	box-sizing: border-box;
	overflow: hidden;''',
    '''	width: 100%;
	height: calc(100vh - 4.5rem);
	box-sizing: border-box;
	overflow: hidden;'''
)

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(content)

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    k_content = f.read()

k_content = k_content.replace(
    '''  flex-direction: column;
  height: 100vh;
  padding: 1.5rem;
  overflow: hidden;''',
    '''  flex-direction: column;
  height: calc(100vh - 4.5rem);
  padding: 1.5rem;
  overflow: hidden;'''
)

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'w') as f:
    f.write(k_content)
