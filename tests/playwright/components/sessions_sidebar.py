"""Component Object voor de sessiebeheer-sidebar (opslaan, laden, overschrijven)."""
from playwright.sync_api import Page, expect


class SessionsSidebar:
    def __init__(self, page: Page):
        self.page = page
        self.naam_input = page.get_by_label("Sessienaam", exact=True)
        self.opslaan_knop = page.get_by_role("button", name="Opslaan")
        self.save_confirmation = page.get_by_test_id("save-confirmation")
        self.save_error = page.get_by_test_id("save-error")
        self.load_error = page.get_by_test_id("load-error")
        self.session_select = page.get_by_test_id("session-select")
        self.sessions_list = page.get_by_test_id("sessions-list")
        self.sessions_empty = page.get_by_test_id("sessions-empty")
        self.overwrite_dialog = page.get_by_test_id("overwrite-dialog")
        self.bevestig_overschrijven_knop = page.get_by_role("button", name="Ja, overschrijven")
        self.annuleer_overschrijven_knop = page.get_by_role("button", name="Annuleren")
        self.validation_session_name = page.get_by_test_id("validation-session-name")

    # --- Actions ---
    def fill_naam(self, naam: str) -> None:
        self.naam_input.fill(naam)

    def opslaan(self) -> None:
        self.opslaan_knop.click()

    def wacht_op_bevestiging(self) -> None:
        self.save_confirmation.wait_for(state="visible")

    def selecteer_via_dropdown(self, naam: str) -> None:
        self.session_select.select_option(naam)

    def selecteer_via_lijst(self, naam: str) -> None:
        self.sessions_list.get_by_text(naam).click()

    def bevestig_overschrijven(self) -> None:
        self.bevestig_overschrijven_knop.click()

    def annuleer_overschrijven(self) -> None:
        self.annuleer_overschrijven_knop.click()

    # --- Validations ---
    def expect_zichtbaar(self) -> None:
        expect(self.sessions_list).to_be_visible()

    def expect_naam_invoerveld_zichtbaar(self) -> None:
        expect(self.naam_input).to_be_visible()

    def expect_opslaan_knop_zichtbaar(self) -> None:
        expect(self.opslaan_knop).to_be_visible()

    def expect_bevestiging_zichtbaar(self, bevat: str | None = None) -> None:
        expect(self.save_confirmation).to_be_visible()
        if bevat:
            expect(self.save_confirmation).to_contain_text(bevat)

    def expect_opslaan_fout_zichtbaar(self) -> None:
        expect(self.save_error).to_be_visible()

    def expect_laadfout_zichtbaar(self) -> None:
        expect(self.load_error).to_be_visible()

    def expect_overschrijf_dialoog_zichtbaar(self) -> None:
        expect(self.overwrite_dialog).to_be_visible()

    def expect_overschrijf_dialoog_niet_zichtbaar(self) -> None:
        expect(self.overwrite_dialog).not_to_be_visible()

    def expect_validatie_naam_zichtbaar(self) -> None:
        expect(self.validation_session_name).to_be_visible()

    def expect_lijst_bevat(self, tekst: str) -> None:
        expect(self.sessions_list).to_contain_text(tekst)

    def expect_lege_lijst_melding_zichtbaar(self) -> None:
        expect(self.sessions_empty).to_be_visible()
