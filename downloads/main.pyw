import os
import json
import ctypes
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import tempfile

# Voorkom dat meerdere instanties tegelijk draaien (Windows)
_MUTEX = None
if os.name == "nt":
    _MUTEX = ctypes.windll.kernel32.CreateMutexW(None, False, "BirthdayCountdown_SingleInstance_NavarDevos")
    if ctypes.windll.kernel32.GetLastError() == 183:
        raise SystemExit

# ==================================================
# 1. MAP AANMAKEN IN APPDATA/LOCAL
# ==================================================

APPDATA_MAP = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "birthday"
)

os.makedirs(APPDATA_MAP, exist_ok=True)

JSON_BESTAND = os.path.join(APPDATA_MAP, "settings.json")


class BirthdayApp:
    def __init__(self):
        # Standaardinstellingen
        self.settings = {
            "jaar": 2013,
            "maand": 12,
            "dag": 25,
            "uur": 0,
            "minuut": 0,
            "koffie_uur": 15,
            "koffie_minuut": 28
        }

        self.laad_settings()

        # Hoofdvenster
        self.venster = tk.Tk()
        self.venster.title("🎉 Birthday Countdown")
        self.venster.geometry("350x150")
        self.venster.configure(bg="#0b111e")
        self.venster.attributes("-topmost", True)
        self.venster.withdraw()

        self.is_zichtbaar = False
        self.a_ingedrukt = False
        self.s_ingedrukt = False
        self.koffie_melding_getoond = None

        # Leeftijd
        self.label_leeftijd = tk.Label(
            self.venster,
            text="",
            font=("Arial", 12),
            fg="#8ba4c7",
            bg="#0b111e"
        )
        self.label_leeftijd.pack(pady=10)

        # Aftelklok
        self.label_tijd = tk.Label(
            self.venster,
            text="",
            font=("Helvetica", 24, "bold"),
            fg="#00e5ff",
            bg="#0b111e"
        )
        self.label_tijd.pack(pady=10)

        # Start de controles
        self.achtergrond_loop()
        self.check_keyboard_loop()

        self.venster.mainloop()

    # ==================================================
    # 2. INSTELLINGEN LADEN
    # ==================================================

    def laad_settings(self):
        """Laad instellingen uit settings.json, of maak het bestand aan."""
        if os.path.exists(JSON_BESTAND):
            try:
                with open(JSON_BESTAND, "r", encoding="utf-8") as bestand:
                    opgeslagen = json.load(bestand)

                if not isinstance(opgeslagen, dict):
                    raise ValueError("JSON bevat geen instellingen-object.")

                for sleutel in self.settings:
                    if sleutel in opgeslagen:
                        self.settings[sleutel] = int(opgeslagen[sleutel])

            except (ValueError, KeyError, OSError, json.JSONDecodeError, TypeError):
                # Bij een beschadigd bestand bewaren we de standaardinstellingen
                # in een nieuw, geldig JSON-bestand.
                self.save_settings()
        else:
            self.save_settings()

    # ==================================================
    # 3. INSTELLINGEN OPSLAAN
    # ==================================================

    def save_settings(self):
        """Sla instellingen veilig op in AppData\\Local\\birthday\\settings.json."""
        os.makedirs(APPDATA_MAP, exist_ok=True)
        tijdelijk_pad = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=APPDATA_MAP,
                prefix="settings_",
                suffix=".tmp",
                delete=False
            ) as bestand:
                tijdelijk_pad = bestand.name
                json.dump(self.settings, bestand, ensure_ascii=False, indent=4)
                bestand.write("\n")
                bestand.flush()
                os.fsync(bestand.fileno())

            os.replace(tijdelijk_pad, JSON_BESTAND)

            # Controleer dat het bestand terug kan worden gelezen en waarden bevat.
            with open(JSON_BESTAND, "r", encoding="utf-8") as controle:
                opgeslagen = json.load(controle)

            if not isinstance(opgeslagen, dict) or not opgeslagen:
                raise OSError("Het JSON-bestand bevat geen instellingen.")

            print(f"Instellingen opgeslagen: {JSON_BESTAND}")

        except (OSError, TypeError, ValueError) as fout:
            if tijdelijk_pad and os.path.exists(tijdelijk_pad):
                try:
                    os.remove(tijdelijk_pad)
                except OSError:
                    pass
            raise OSError(
                f"Opslaan van instellingen.json is mislukt.\\n"
                f"Bestand: {JSON_BESTAND}\\nFout: {fout}"
            ) from fout

    # ==================================================
    # 4. INSTELLINGENVENSTER
    # ==================================================

    def open_settings_window(self):
        bestaand = getattr(self, "settings_win", None)
        if bestaand is not None:
            try:
                if bestaand.winfo_exists():
                    bestaand.lift()
                    bestaand.focus_force()
                    return
            except tk.TclError:
                pass

        settings_win = tk.Toplevel(self.venster)
        self.settings_win = settings_win
        settings_win.title("⚙️ App Settings")
        settings_win.geometry("340x365")
        settings_win.configure(bg="#1a2333")
        settings_win.attributes("-topmost", True)
        settings_win.resizable(False, False)

        velden = [
            ("Geboortejaar:", "jaar"),
            ("Geboortemaand (1-12):", "maand"),
            ("Geboortedag (1-31):", "dag"),
            ("Geboorte-uur (0-23):", "uur"),
            ("Geboorteminuut (0-59):", "minuut"),
            ("Koffietijd uur (0-23):", "koffie_uur"),
            ("Koffietijd minuut (0-59):", "koffie_minuut")
        ]

        entries = {}

        for label_tekst, sleutel in velden:
            frame = tk.Frame(
                settings_win,
                bg="#1a2333"
            )
            frame.pack(fill="x", padx=12, pady=5)

            lbl = tk.Label(
                frame,
                text=label_tekst,
                fg="#ffffff",
                bg="#1a2333",
                width=21,
                anchor="w"
            )
            lbl.pack(side="left")

            ent = tk.Entry(
                frame,
                bg="#2d3748",
                fg="#00e5ff",
                insertbackground="#00e5ff",
                width=8
            )
            ent.insert(0, str(self.settings[sleutel]))
            ent.pack(side="right")

            entries[sleutel] = ent

        def opslaan():
            try:
                nieuwe_settings = {}

                for sleutel, entry in entries.items():
                    nieuwe_settings[sleutel] = int(entry.get())

                # Controleer de waarden
                if not 1 <= nieuwe_settings["maand"] <= 12:
                    raise ValueError("De maand moet tussen 1 en 12 liggen.")

                if not 0 <= nieuwe_settings["uur"] <= 23:
                    raise ValueError("Het geboorte-uur moet tussen 0 en 23 liggen.")

                if not 0 <= nieuwe_settings["minuut"] <= 59:
                    raise ValueError("De geboorteminuut moet tussen 0 en 59 liggen.")

                if not 0 <= nieuwe_settings["koffie_uur"] <= 23:
                    raise ValueError("Het koffie-uur moet tussen 0 en 23 liggen.")

                if not 0 <= nieuwe_settings["koffie_minuut"] <= 59:
                    raise ValueError("De koffieminuut moet tussen 0 en 59 liggen.")

                if not 1 <= nieuwe_settings["dag"] <= 31:
                    raise ValueError("De dag moet tussen 1 en 31 liggen.")

                if not 1 <= nieuwe_settings["jaar"] <= 9999:
                    raise ValueError("Vul een geldig geboortejaar in.")

                # Controleer of de geboortedatum echt bestaat
                datetime(
                    nieuwe_settings["jaar"],
                    nieuwe_settings["maand"],
                    nieuwe_settings["dag"]
                )

                # Pas de instellingen pas toe als alles geldig is
                self.settings.update(nieuwe_settings)
                self.save_settings()

                messagebox.showinfo(
                    "Succes",
                    f"Instellingen opgeslagen in:\n{JSON_BESTAND}",
                    parent=settings_win
                )

                settings_win.destroy()

            except ValueError as fout:
                messagebox.showerror(
                    "Ongeldige instellingen",
                    str(fout) if str(fout) else "Vul alleen geldige gehele getallen in.",
                    parent=settings_win
                )

            except OSError as fout:
                messagebox.showerror(
                    "Opslaan mislukt",
                    f"De instellingen konden niet worden opgeslagen:\n{fout}",
                    parent=settings_win
                )

        btn_save = tk.Button(
            settings_win,
            text="💾 Instellingen Opslaan",
            bg="#00e5ff",
            fg="#0b111e",
            font=("Arial", 10, "bold"),
            command=opslaan
        )
        btn_save.pack(pady=15)

    # ==================================================
    # 5. KLOK TONEN OF VERBERGEN
    # ==================================================

    def toggle_venster(self):
        if self.is_zichtbaar:
            self.venster.withdraw()
            self.is_zichtbaar = False
        else:
            self.venster.deiconify()
            self.venster.lift()
            self.venster.attributes("-topmost", True)
            self.is_zichtbaar = True

    # ==================================================
    # 6. GLOBALE SNELTOETSEN
    # CTRL + SHIFT + A = KLOK TONEN/VERBERGEN
    # CTRL + SHIFT + S = INSTELLINGEN
    # ==================================================

    def check_keyboard_loop(self):
        try:
            ctrl = ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000
            shift = ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000
            a_toets = ctypes.windll.user32.GetAsyncKeyState(0x41) & 0x8000
            s_toets = ctypes.windll.user32.GetAsyncKeyState(0x53) & 0x8000

            if ctrl and shift:
                if a_toets:
                    if not self.a_ingedrukt:
                        self.toggle_venster()
                        self.a_ingedrukt = True
                else:
                    self.a_ingedrukt = False

                if s_toets:
                    if not self.s_ingedrukt:
                        self.open_settings_window()
                        self.s_ingedrukt = True
                else:
                    self.s_ingedrukt = False
            else:
                self.a_ingedrukt = False
                self.s_ingedrukt = False

        except Exception:
            pass

        self.venster.after(50, self.check_keyboard_loop)

    # ==================================================
    # 7. LIVE AFTELKLOK EN KOFFIEMELDING
    # ==================================================

    def achtergrond_loop(self):
        nu = datetime.now()

        try:
            maand = self.settings["maand"]
            dag = self.settings["dag"]
            uur = self.settings["uur"]
            minuut = self.settings["minuut"]

            # Bepaal de volgende verjaardag
            try:
                volgende = datetime(
                    nu.year,
                    maand,
                    dag,
                    uur,
                    minuut
                )
            except ValueError:
                # Bijvoorbeeld 29 februari in een niet-schrikkeljaar
                volgende = None

            if volgende is None or volgende < nu:
                jaar = nu.year + 1

                while True:
                    try:
                        volgende = datetime(
                            jaar,
                            maand,
                            dag,
                            uur,
                            minuut
                        )
                        break
                    except ValueError:
                        jaar += 1

            verschil = volgende - nu

            dagen = verschil.days
            uren, rest = divmod(verschil.seconds, 3600)
            minuten, seconden = divmod(rest, 60)

            self.label_tijd.config(
                text=f"{dagen}d {uren:02d}u {minuten:02d}m {seconden:02d}s"
            )

            # Bereken de leeftijd op basis van de geboortedatum
            geboortejaar = self.settings["jaar"]
            verjaardag_geweest = (
                (nu.month, nu.day) >= (maand, dag)
            )

            leeftijd = (
                nu.year
                - geboortejaar
                - (0 if verjaardag_geweest else 1)
            )

            self.label_leeftijd.config(
                text=f"Huidige leeftijd: {leeftijd} jaar"
            )

        except Exception:
            pass

        # Koffiemelding maximaal één keer per dag
        koffie_uur = self.settings["koffie_uur"]
        koffie_minuut = self.settings["koffie_minuut"]

        if (
            nu.hour == koffie_uur
            and nu.minute == koffie_minuut
            and self.koffie_melding_getoond != nu.date()
        ):
            self.koffie_melding_getoond = nu.date()

            messagebox.showinfo(
                "☕ Geheime Koffie Break!",
                "Koffietijd!\n"
                "Tijd voor een oranje fles Nescafé met havermelk "
                "en chocomelkpoeder! ☕🍊\n\n"
                "Das echt lekker!",
                parent=self.venster
            )

        self.venster.after(1000, self.achtergrond_loop)


# ==================================================
# 8. APP STARTEN
# ==================================================

if __name__ == "__main__":
    BirthdayApp()