import tkinter as tk
from tkinter import messagebox, filedialog
import ast
import operator as op
import random
import datetime

# sympy za jednačine
from sympy import symbols, Eq, solve, sympify

# --------------------------
# SIGURNO EVALUACIJA IZRAZA
# --------------------------
# Dozvoljeni operatori
ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

def safe_eval(node):
    """
    Rekurzivno proceni AST čvor za bezbednu aritmetiku.
    Podržava: + - * / ** % i zagrade i numeričke literale.
    """
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    if isinstance(node, ast.Num):  # Python <3.8
        return node.n
    if hasattr(ast, "Constant") and isinstance(node, ast.Constant):  # Python 3.8+
        if isinstance(node.value, (int, float)):
            return node.value
        else:
            raise ValueError("Dozvoljeni su samo brojevi.")
    if isinstance(node, ast.BinOp):
        if type(node.op) not in ALLOWED_OPERATORS:
            raise ValueError("Operator nije dozvoljen.")
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        return ALLOWED_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp):
        if type(node.op) not in ALLOWED_OPERATORS:
            raise ValueError("Operator nije dozvoljen.")
        operand = safe_eval(node.operand)
        return ALLOWED_OPERATORS[type(node.op)](operand)
    raise ValueError("Nevažeći izraz.")

def evaluate_expression(expr_str):
    """
    Sigurno evaluira aritmetički izraz.
    """
    try:
        # zamenimo ^ sa ** ako korisnik unese
        expr_str = expr_str.replace('^', '**')
        tree = ast.parse(expr_str, mode='eval')
        return safe_eval(tree)
    except Exception as e:
        raise ValueError(f"Nevažeći izraz ili operator: {e}")

# --------------------------
# JEDNAČINE (sympy)
# --------------------------
def solve_equation(equation_str):
    """
    Rešava jednačine koje korisnik unese, npr:
      3*x - 6 = 12
      x**2 - 5*x + 6 = 0
      system: ["2*x + y = 5", "x - y = 1"]  -> ne koristi se ovde, ali sympy podržava
    Vraća string sa rešenjem.
    """
    try:
        # normalize
        equation_str = equation_str.replace('^', '**')
        if '=' not in equation_str:
            raise ValueError("Jednačina mora sadržati '='.")
        left_s, right_s = equation_str.split('=', 1)
        # sympify
        left = sympify(left_s)
        right = sympify(right_s)
        # pokušaj prepoznati promenljive
        vars = list(left.free_symbols.union(right.free_symbols))
        if not vars:
            # nema promenljive
            val = (left - right).evalf()
            if abs(val) < 1e-9:
                return "Istinitost: identično tačno (nema promenljivih)."
            else:
                return "Nema rešenja (nije jednako)."
        sol = solve(Eq(left, right), vars)
        return f"Rešenje: {sol}"
    except Exception as e:
        return f"Greška pri rešavanju: {e}"

# --------------------------
# TEKSTUALNI PROBLEMI (jednostavni)
# --------------------------
def solve_text_problem(text):
    """
    Vrlo jednostavno prepoznavanje par tipova zadataka:
     - brzina i vreme: "Auto ide 60 km/h koliko pređe za 2 sata"
     - oblast pravougaonika: "stranice 5 i 3, povrsina"
    Ovo je heuristika, ne razume sve.
    """
    t = text.lower()
    # brzina-km/h i sati
    if "km/h" in t or "kmh" in t or ("km" in t and "h" in t):
        try:
            # pronađi brojeve u tekstu (jednostavno)
            nums = [int(s) for s in "".join(c if (c.isdigit() or c.isspace()) else " " for c in t).split() if s.strip()]
            if len(nums) >= 2:
                speed = nums[0]
                time = nums[1]
                return f"Rezultat: {speed * time} (km)"
        except:
            pass
    # površina pravougaonika
    if "povrsin" in t or "površin" in t or "area" in t:
        try:
            nums = [int(s) for s in "".join(c if (c.isdigit() or c.isspace()) else " " for c in t).split() if s.strip()]
            if len(nums) >= 2:
                return f"Površina = {nums[0] * nums[1]}"
        except:
            pass
    return "Ne mogu automatski rešiti ovaj tekstualni zadatak (probaj preciznije)."

# --------------------------
# GLAZURA (tkinter GUI)
# --------------------------
class SmartCalcApp:
    def __init__(self, root):
        self.root = root
        root.title("Pametni kalkulator - GUI (izrazi + jednačine + tekst)")
        root.geometry("700x480")

        # Naslov
        title = tk.Label(root, text="Pametni kalkulator - Rešava izraze, jednačine i jednostavne tekstualne zadatke", wraplength=680, justify="center", font=("Arial", 11, "bold"))
        title.pack(pady=8)

        # Frame za unos
        frm = tk.Frame(root)
        frm.pack(pady=6, padx=10, fill="x")

        tk.Label(frm, text="Mod:").grid(row=0, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="Izraz")
        mode_menu = tk.OptionMenu(frm, self.mode_var, "Izraz", "Jednačina", "Tekstualni")
        mode_menu.grid(row=0, column=1, sticky="w", padx=6)

        tk.Label(frm, text="Unesi zadatak:").grid(row=1, column=0, sticky="nw", pady=6)
        self.input_text = tk.Text(frm, height=4, width=70, font=("Arial", 11))
        self.input_text.grid(row=1, column=1, columnspan=3, pady=6)

        # Dugmad
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=6)
        solve_btn = tk.Button(btn_frame, text="Reši", width=12, command=self.solve)
        solve_btn.grid(row=0, column=0, padx=6)
        clear_btn = tk.Button(btn_frame, text="Obriši", width=12, command=self.clear_input)
        clear_btn.grid(row=0, column=1, padx=6)
        save_btn = tk.Button(btn_frame, text="Sačuvaj istoriju", width=14, command=self.save_history)
        save_btn.grid(row=0, column=2, padx=6)
        demo_btn = tk.Button(btn_frame, text="Primer zadatka", width=14, command=self.insert_demo)
        demo_btn.grid(row=0, column=3, padx=6)

        # Rezultat
        tk.Label(root, text="Rezultat / Objašnjenje:", font=("Arial", 10, "bold")).pack(anchor="w", padx=12)
        self.result_label = tk.Label(root, text="", wraplength=660, justify="left", font=("Arial", 11))
        self.result_label.pack(padx=12, pady=6, anchor="w")

        # Istorija
        tk.Label(root, text="Istorija:", font=("Arial", 10, "bold")).pack(anchor="w", padx=12)
        self.history_text = tk.Text(root, height=10, width=85, state="disabled", font=("Courier", 10))
        self.history_text.pack(padx=12, pady=6)

        # intern
        self.history = []

    def insert_demo(self):
        mode = self.mode_var.get()
        if mode == "Izraz":
            s = "(5 + 3) * 2 - 4^2"
        elif mode == "Jednačina":
            s = "3*x - 6 = 12"
        else:
            s = "Auto ide 60 km/h koliko pređe za 2 sata?"
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, s)

    def clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.result_label.config(text="")

    def append_history(self, mode, query, result):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] ({mode}) {query} -> {result}\n"
        self.history.append(line)
        self.history_text.config(state="normal")
        self.history_text.insert(tk.END, line)
        self.history_text.config(state="disabled")

    def save_history(self):
        if not self.history:
            messagebox.showinfo("Sačuvaj", "Istorija je prazna.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(self.history)
            messagebox.showinfo("Sačuvaj", f"Istorija sačuvana u {path}")

    def solve(self):
        mode = self.mode_var.get()
        query = self.input_text.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Upozorenje", "Unesi zadatak prvo.")
            return

        if mode == "Izraz":
            try:
                res = evaluate_expression(query)
                out = f"{res}"
                self.result_label.config(text=f"Rezultat: {out}")
            except Exception as e:
                out = f"Greška: {e}"
                self.result_label.config(text=out)
        elif mode == "Jednačina":
            out = solve_equation(query)
            self.result_label.config(text=out)
        else:  # tekstualni
            out = solve_text_problem(query)
            self.result_label.config(text=out)

        self.append_history(mode, query, out)

# --------------------------
# Pokretanje aplikacije
# --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SmartCalcApp(root)
    root.mainloop()
