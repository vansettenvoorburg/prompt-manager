"""Component Object voor de Instellingen-tab (rate limiting per provider)."""
from playwright.sync_api import Page, expect


class SettingsPanel:
    def __init__(self, page: Page):
        self.page = page
        self.root = page.locator("[data-testid=instellingen-paneel]")
        self.groq_rpm_input = page.locator("[data-testid=groq-rpm-input]")
        self.google_rpm_input = page.locator("[data-testid=google-rpm-input]")
        self.ollama_rpm_input = page.locator("[data-testid=ollama-rpm-input]")
        self.opslaan_knop = page.get_by_role("button", name="Instellingen opslaan")
        self.bevestiging = page.locator("[data-testid=instellingen-bevestiging]")
        self.fout = page.locator("[data-testid=instellingen-fout]")

    # --- Actions ---
    def fill_groq_rpm(self, waarde: str) -> None:
        self.groq_rpm_input.fill(waarde)

    def fill_google_rpm(self, waarde: str) -> None:
        self.google_rpm_input.fill(waarde)

    def opslaan(self) -> None:
        self.opslaan_knop.click()

    # --- Validations ---
    def expect_zichtbaar(self) -> None:
        expect(self.root).to_be_visible()

    def expect_groq_rpm_veld_zichtbaar(self) -> None:
        expect(self.groq_rpm_input).to_be_visible()

    def expect_google_rpm_veld_zichtbaar(self) -> None:
        expect(self.google_rpm_input).to_be_visible()

    def expect_ollama_rpm_veld_niet_aanwezig(self) -> None:
        expect(self.ollama_rpm_input).not_to_be_attached()

    def expect_groq_rpm_waarde(self, waarde: str) -> None:
        assert self.groq_rpm_input.input_value() == waarde, (
            f"Verwacht {waarde!r} als Groq RPM, maar kreeg {self.groq_rpm_input.input_value()!r}"
        )

    def expect_google_rpm_waarde(self, waarde: str) -> None:
        assert self.google_rpm_input.input_value() == waarde, (
            f"Verwacht {waarde!r} als Google RPM, maar kreeg {self.google_rpm_input.input_value()!r}"
        )

    def expect_bevestiging_zichtbaar(self) -> None:
        expect(self.bevestiging).to_be_visible()

    def expect_fout_zichtbaar(self) -> None:
        expect(self.fout).to_be_visible()
