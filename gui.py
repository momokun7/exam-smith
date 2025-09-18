import tkinter as tk
from tkinter import ttk, messagebox
from prompts import build_descriptive_prompt, build_multiple_choice_prompt
from config import (
    WINDOW_TITLE,
    WINDOW_GEOMETRY,
    DIFFICULTY_OPTIONS,
    QUESTION_TYPE_OPTIONS,
    DEFAULT_DIFFICULTY,
    DEFAULT_QUESTION_TYPE,
    DEFAULT_NUM_CHOICES,
    CHOICES_MIN,
    CHOICES_MAX,
    WIDTH_DIFFICULTY,
    WIDTH_QUESTION_TYPE,
    WIDTH_WORD_LIMIT,
)
from validators import digits_only
import re

class QuestionCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)

        # プロンプト生成フラグ
        self.prompt_generated = False

        # メインフレーム
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # タイトル
        title_label = ttk.Label(main_frame, text="試験問題作成", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 難易度選択
        ttk.Label(main_frame, text="難易度:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.difficulty_var = tk.StringVar()
        difficulty_combo = ttk.Combobox(main_frame, textvariable=self.difficulty_var, state="readonly", width=WIDTH_DIFFICULTY)
        difficulty_combo['values'] = DIFFICULTY_OPTIONS
        difficulty_combo.grid(row=1, column=1, sticky=(tk.W), pady=5, padx=(10, 0))
        difficulty_combo.set(DEFAULT_DIFFICULTY)  # デフォルト値

        # 問題形式選択
        ttk.Label(main_frame, text="問題形式:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.question_type_var = tk.StringVar()
        question_type_combo = ttk.Combobox(main_frame, textvariable=self.question_type_var, state="readonly", width=WIDTH_QUESTION_TYPE)
        question_type_combo['values'] = QUESTION_TYPE_OPTIONS
        question_type_combo.grid(row=2, column=1, sticky=(tk.W), pady=5, padx=(10, 0))
        question_type_combo.set(DEFAULT_QUESTION_TYPE)
        question_type_combo.bind('<<ComboboxSelected>>', lambda e: self.update_choice_controls())

        # 問題数（固定5のため非表示）
        self.num_questions_label = ttk.Label(main_frame, text="問題数:")
        self.num_questions_var = tk.IntVar(value=5)
        self.num_questions_spin = ttk.Spinbox(main_frame, from_=5, to=10, textvariable=self.num_questions_var, width=10, state='disabled')

        # 選択肢数（多肢択一の場合のみ表示）
        self.num_choices_label = ttk.Label(main_frame, text="選択肢数:")
        self.num_choices_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        self.num_choices_var = tk.IntVar(value=DEFAULT_NUM_CHOICES)
        self.num_choices_spin = ttk.Spinbox(main_frame, from_=CHOICES_MIN, to=CHOICES_MAX, textvariable=self.num_choices_var, width=10, state='disabled')
        self.num_choices_spin.grid(row=4, column=1, sticky=(tk.W), pady=5, padx=(10, 0))

        # 字数制限（記述式の場合のみ表示）
        self.word_limit_label = ttk.Label(main_frame, text="字数制限:")
        self.word_limit_label.grid(row=5, column=0, sticky=tk.W, pady=5)
        self.word_limit_var = tk.StringVar()
        self.word_limit_entry = ttk.Entry(main_frame, textvariable=self.word_limit_var, width=WIDTH_WORD_LIMIT)
        self.word_limit_entry.grid(row=5, column=1, sticky=(tk.W), pady=5, padx=(10, 0))

        # 字数制限の説明
        self.word_limit_help = ttk.Label(main_frame, text="※ なしの場合は空欄にしてください", font=("Arial", 8))
        self.word_limit_help.grid(row=6, column=1, sticky=tk.W, pady=(0, 10), padx=(10, 0))

        # 問題文
        ttk.Label(main_frame, text="問題文:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.problem_text = tk.Text(main_frame, height=10, width=50, wrap=tk.WORD)
        self.problem_text.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        # スクロールバー
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.problem_text.yview)
        scrollbar.grid(row=7, column=2, sticky=(tk.N, tk.S))
        self.problem_text.configure(yscrollcommand=scrollbar.set)

        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)

        # 生成ボタン
        generate_button = ttk.Button(button_frame, text="プロンプト生成", command=self.generate_prompt)
        generate_button.pack(side=tk.LEFT, padx=5)

        # クリアボタン
        clear_button = ttk.Button(button_frame, text="クリア", command=self.clear_form)
        clear_button.pack(side=tk.LEFT, padx=5)

        # 直接コピーボタン
        self.direct_copy_button = ttk.Button(button_frame, text="プロンプトをコピー", command=self.direct_copy_prompt, state="disabled")
        self.direct_copy_button.pack(side=tk.LEFT, padx=5)

        # ステータス表示エリア
        self.status_label = ttk.Label(main_frame, text="プロンプトを生成してください", font=("Arial", 10), foreground="gray")
        self.status_label.grid(row=9, column=0, columnspan=2, pady=(20, 5))

        # 結果表示エリア（非表示）
        self.result_frame = ttk.Frame(main_frame)
        self.result_frame.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.result_frame.grid_remove()  # 初期状態では非表示

        ttk.Label(self.result_frame, text="生成されたプロンプト:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.result_text = tk.Text(self.result_frame, height=8, width=50, wrap=tk.WORD)
        self.result_text.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # 結果エリアのスクロールバー
        result_scrollbar = ttk.Scrollbar(self.result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        result_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.result_text.configure(yscrollcommand=result_scrollbar.set)

        # グリッドの重み設定
        main_frame.columnconfigure(1, weight=1)
        self.result_frame.columnconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # 字数制限の入力検証
        self.word_limit_var.trace('w', self.validate_word_limit)

        # 生成されたプロンプトを保存
        self.generated_prompt = ""

        # 初期状態のコントロール有効/無効を更新
        self.update_choice_controls()

    def validate_word_limit(self, *args):
        """字数制限の入力検証"""
        value = self.word_limit_var.get()
        self.word_limit_var.set(digits_only(value))

    def update_choice_controls(self):
        """問題形式に応じて選択肢数の入力可否を切り替え"""
        qtype = self.question_type_var.get()
        if qtype == '多肢択一':
            # 選択肢数を表示、字数制限を非表示
            self.num_choices_label.grid()  # 以前の配置を復元（row=4）
            self.num_choices_spin.grid()
            self.num_choices_spin.config(state='normal')

            self.word_limit_label.grid_remove()
            self.word_limit_entry.grid_remove()
            self.word_limit_help.grid_remove()
        else:
            # 記述式: 字数制限を表示、選択肢数を非表示
            self.word_limit_label.grid()
            self.word_limit_entry.grid()
            self.word_limit_help.grid()

            self.num_choices_label.grid_remove()
            self.num_choices_spin.grid_remove()

    def generate_prompt(self):
        """プロンプトを生成"""
        difficulty = self.difficulty_var.get()
        word_limit = self.word_limit_var.get()
        problem_text = self.problem_text.get("1.0", tk.END).strip()
        question_type = self.question_type_var.get()
        num_choices = self.num_choices_var.get()

        if not problem_text:
            messagebox.showerror("エラー", "問題文を入力してください。")
            return

        # 字数制限の処理
        word_limit_text = word_limit if word_limit else "なし"

        # プロンプト（記述式）
        prompt_descrive_form = build_descriptive_prompt(word_limit_text=word_limit_text, problem_text=problem_text)

        # プロンプト（多肢択一）
        prompt_multiple_choice_form = build_multiple_choice_prompt(num_choices=num_choices, problem_text=problem_text)


        # 選択に応じてプロンプトを決定
        if question_type == '多肢択一':
            prompt = prompt_multiple_choice_form
        else:
            prompt = prompt_descrive_form

        # 生成されたプロンプトを保存
        self.generated_prompt = prompt
        self.prompt_generated = True

        # UIを更新
        self.status_label.config(text="プロンプトが生成されました！コピーボタンを押してコピーしてください。", foreground="green")
        self.direct_copy_button.config(state="normal")

        # 結果を表示（オプション）
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", prompt)
        self.result_frame.grid()  # 結果エリアを表示

    def clear_form(self):
        """フォームをクリア"""
        self.difficulty_var.set(DEFAULT_DIFFICULTY)
        self.word_limit_var.set('')
        self.question_type_var.set(DEFAULT_QUESTION_TYPE)
        self.num_choices_var.set(DEFAULT_NUM_CHOICES)
        self.num_questions_var.set(5)
        self.problem_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
        self.result_frame.grid_remove()  # 結果エリアを非表示

        # 状態をリセット
        self.prompt_generated = False
        self.generated_prompt = ""
        self.status_label.config(text="プロンプトを生成してください", foreground="gray")
        self.direct_copy_button.config(state="disabled")
        self.update_choice_controls()

    def direct_copy_prompt(self):
        """プロンプトを直接クリップボードにコピー"""
        if not self.prompt_generated or not self.generated_prompt:
            messagebox.showwarning("警告", "先にプロンプトを生成してください。")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(self.generated_prompt)
        messagebox.showinfo("完了", "プロンプトをクリップボードにコピーしました。")

        # 成功メッセージを更新
        self.status_label.config(text="プロンプトがコピーされました！", foreground="blue")

def main():
    root = tk.Tk()
    app = QuestionCreatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
