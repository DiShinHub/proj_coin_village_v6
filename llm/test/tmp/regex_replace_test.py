from app.tool.properties_tool import PropertiesTool

string = "test${APP_NAME}/${APP_P2ATH:-default_value:-default_value:-default_value}/${APP_PATH3}/${APP_PATH}/${APP_PATH}/${APP_PATH}"

print(PropertiesTool.replace_value_to_os_env_var(target_value=string))
