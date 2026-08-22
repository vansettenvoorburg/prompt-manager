"""Page Object voor de hoofdpagina van de Prompt Sessie Manager (single-page app)."""
from playwright.sync_api import Page, expect

from tests.playwright.components.reviewer_list import ReviewerList
from tests.playwright.components.sessions_sidebar import SessionsSidebar
from tests.playwright.components.settings_panel import SettingsPanel
from tests.playwright.mocks import DEFAULT_DOEL, DEFAULT_ROL, DEFAULT_TAAK


class PromptPage:
    def __init__(self, page: Page):
        self.page = page
        self.sidebar = SessionsSidebar(page)
        self.instellingen = SettingsPanel(page)
        self.reviewers = ReviewerList(page)

        self.rol_input = page.locator("[name=rol]")
        self.taak_input = page.locator("[name=taak]")
        self.doel_input = page.locator("[name=doel]")
        self.formaat_input = page.locator("[name=formaat]")
        self.stijl_input = page.locator("[name=stijl]")
        self.scope_input = page.locator("[name=scope]")
        self.eisen_input = page.locator("[name=eisen]")
        self.voorbeelden_input = page.locator("[name=voorbeelden]")
        self._veld_inputs = {
            "rol": self.rol_input,
            "taak": self.taak_input,
            "doel": self.doel_input,
            "formaat": self.formaat_input,
            "stijl": self.stijl_input,
            "scope": self.scope_input,
            "eisen": self.eisen_input,
            "voorbeelden": self.voorbeelden_input,
        }

        self.provider_select = page.locator("[data-testid=provider-select]")
        self.groq_model_select = page.locator("[data-testid=groq-model-select]")
        self.runs_input = page.locator("[data-testid=runs-input]")
        self.temperature_input = page.locator("[data-testid=temperature-input]")
        self.temperature_modus_alle = page.locator("[data-testid=temperature-modus-alle]")
        self.temperature_modus_per_run = page.locator("[data-testid=temperature-modus-per-run]")
        self.temperature_modus = page.locator("[data-testid=temperature-modus]")
        self.temperature_label = page.locator("[data-testid=temperature-label]")

        self.bijlage_input = page.locator("[data-testid=bijlage-input]")
        self.bijlage_status = page.locator("[data-testid=bijlage-status]")
        self.bijlage_verwijder_knop = page.locator("[data-testid=bijlage-verwijder]")

        self.review_modus_select = page.locator("[data-testid=review-modus-select]")
        self.verstuur_knop = page.get_by_role("button", name="Verstuur")

        self.tab_prompt = page.locator("[data-testid=tab-prompt]")
        self.tab_instellingen = page.locator("[data-testid=tab-instellingen]")

        self.loading = page.locator("[data-testid=loading]")
        self.response = page.locator("[data-testid=response]")
        self.run_results = page.locator("[data-testid=run-results]")
        self.eindoutput = page.locator("[data-testid=eindoutput]")
        self.error = page.locator("[data-testid=error]")
        self.log_status = page.locator("[data-testid=log-status]")
        self.log_warning = page.locator("[data-testid=log-warning]")

    # --- Actions ---
    def open(self, base_url: str) -> None:
        self.page.goto(base_url)

    def reload(self) -> None:
        self.page.reload()

    def fill_veld(self, veld: str, waarde: str) -> None:
        self._veld_inputs[veld].fill(waarde)

    def vul_verplichte_velden(
        self,
        *,
        rol: str = DEFAULT_ROL,
        taak: str = DEFAULT_TAAK,
        doel: str = DEFAULT_DOEL,
        uitzondering: str | None = None,
    ) -> None:
        for veld, waarde in (("rol", rol), ("taak", taak), ("doel", doel)):
            if veld != uitzondering:
                self.fill_veld(veld, waarde)

    def kies_provider(self, provider: str) -> None:
        self.provider_select.select_option(provider)

    def kies_groq_model(self, model: str) -> None:
        self.groq_model_select.select_option(model)

    def fill_runs(self, aantal) -> None:
        self.runs_input.fill(str(aantal))

    def kies_temperature_modus_per_run(self) -> None:
        self.temperature_modus_per_run.click()

    def fill_temperature(self, waarde: str) -> None:
        self.temperature_input.fill(waarde)

    def upload_bijlage(self, pad: str) -> None:
        self.bijlage_input.set_input_files(pad)

    def verwijder_bijlage(self) -> None:
        self.bijlage_verwijder_knop.click()

    def verstuur(self) -> None:
        self.verstuur_knop.click()

    def open_tab_instellingen(self) -> None:
        self.tab_instellingen.click()

    def mock_clipboard_succesvol(self) -> None:
        self.page.evaluate("navigator.clipboard = { writeText: (t) => Promise.resolve() }")

    def mock_clipboard_mislukt(self) -> None:
        self.page.evaluate(
            "navigator.clipboard = { writeText: (t) => Promise.reject(new Error('geen toestemming')) }"
        )

    def eerste_kopieer_knop(self, binnen: str = "run-results"):
        return self.page.locator(f"[data-testid={binnen}] [data-testid=kopieer-knop]").first

    # --- Validations ---
    def expect_veld_zichtbaar(self, veld: str) -> None:
        expect(self._veld_inputs[veld]).to_be_visible()

    def expect_veld_waarde(self, veld: str, waarde: str) -> None:
        expect(self._veld_inputs[veld]).to_have_value(waarde)

    def expect_validation_zichtbaar(self, veld: str) -> None:
        expect(self.page.locator(f"[data-testid=validation-{veld}]")).to_be_visible()

    def expect_error_zichtbaar(self) -> None:
        expect(self.error).to_be_visible()

    def expect_error_niet_zichtbaar(self) -> None:
        expect(self.error).not_to_be_visible()

    def expect_error_bevat(self, tekst: str) -> None:
        expect(self.error).to_contain_text(tekst)

    def expect_error_niet_leeg(self) -> None:
        expect(self.error).not_to_be_empty()

    def expect_response_bevat_niet(self, tekst: str) -> None:
        expect(self.response).not_to_contain_text(tekst)

    def expect_run_results_zichtbaar(self) -> None:
        expect(self.run_results).to_be_visible()

    def expect_run_results_bevat(self, tekst: str) -> None:
        expect(self.run_results).to_contain_text(tekst)

    def expect_eindoutput_zichtbaar(self) -> None:
        expect(self.eindoutput).to_be_visible()

    def expect_reviewer_stap_zichtbaar(self) -> None:
        expect(self.page.locator("[data-testid=reviewer-stap-item]").first).to_be_visible()

    def expect_loading_zichtbaar(self) -> None:
        expect(self.loading).to_be_visible()

    def expect_provider_waarde(self, waarde: str) -> None:
        geselecteerd = self.provider_select.input_value()
        assert geselecteerd.lower() == waarde.lower(), (
            f"Verwacht provider {waarde!r}, kreeg: {geselecteerd!r}"
        )

    def expect_temperature_waarde(self, *mogelijke_waarden: str) -> None:
        werkelijk = self.temperature_input.input_value()
        assert werkelijk in mogelijke_waarden, (
            f"Verwacht temperature in {mogelijke_waarden!r}, kreeg: {werkelijk!r}"
        )

    def expect_groq_model_waarde(self, waarde: str) -> None:
        expect(self.groq_model_select).to_have_value(waarde)

    def expect_groq_model_zichtbaar(self) -> None:
        expect(self.groq_model_select).to_be_visible()

    def expect_groq_model_niet_zichtbaar(self) -> None:
        expect(self.groq_model_select).not_to_be_visible()

    def expect_temperature_modus_per_run_geselecteerd(self) -> None:
        expect(self.temperature_modus_per_run).to_be_checked()

    def expect_groq_model_opties(self) -> list[str]:
        return self.groq_model_select.locator("option").evaluate_all("opts => opts.map(o => o.value)")

    def expect_provider_opties(self) -> list[str]:
        return self.provider_select.locator("option").all_text_contents()

    def expect_bijlage_status_bevat(self, tekst: str) -> None:
        werkelijk = self.bijlage_status.inner_text()
        assert tekst in werkelijk, f"Verwacht {tekst!r} in bijlagestatus, kreeg: {werkelijk!r}"

    def expect_bijlage_verwijder_knop_zichtbaar(self) -> None:
        expect(self.bijlage_verwijder_knop).to_be_visible()

    def expect_bijlage_verwijder_knop_niet_zichtbaar(self) -> None:
        expect(self.bijlage_verwijder_knop).not_to_be_visible()
