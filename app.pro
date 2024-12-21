# app.pro

SOURCES += main.py \
           views/main_window.py \
           views/scenario_manager.py \
           views/status_bar.py \
           views/tabs/tab_widget.py \
           views/tabs/element_setting.py \
           views/tabs/model_generation.py \
           views/tabs/model_transformation.py \
           views/tabs/condition_setting.py \
           views/dialogs/custom_error_dialog.py \
           views/dialogs/custom_information_dialog.py \
           views/dialogs/custom_question_dialog.py \
           views/dialogs/custom_warning_dialog.py

TRANSLATIONS = translations_zh_CN.ts translations_en_US.ts