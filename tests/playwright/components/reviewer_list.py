"""Component Object voor de herhaalde reviewer-items in het promptformulier."""
from playwright.sync_api import Locator, Page, expect


class ReviewerItem:
    def __init__(self, root: Locator):
        self.root = root
        self.rol_input = root.get_by_test_id("reviewer-rol")
        self.omschrijving_input = root.get_by_test_id("reviewer-omschrijving")
        self.runs_input = root.get_by_test_id("reviewer-runs")
        self.temperatures_input = root.get_by_test_id("reviewer-temperatures")
        self.verwijder_knop = root.get_by_test_id("reviewer-verwijder")

    # --- Actions ---
    def fill_rol(self, waarde: str) -> None:
        self.rol_input.fill(waarde)

    def fill_omschrijving(self, waarde: str) -> None:
        self.omschrijving_input.fill(waarde)

    def verwijder(self) -> None:
        self.verwijder_knop.click()

    # --- Validations ---
    def expect_zichtbaar(self) -> None:
        expect(self.root).to_be_visible()

    def expect_rol_zichtbaar(self) -> None:
        expect(self.rol_input).to_be_visible()

    def expect_omschrijving_zichtbaar(self) -> None:
        expect(self.omschrijving_input).to_be_visible()

    def expect_runs_zichtbaar(self) -> None:
        expect(self.runs_input).to_be_visible()

    def expect_temperatures_zichtbaar(self) -> None:
        expect(self.temperatures_input).to_be_visible()

    def expect_verwijder_knop_zichtbaar(self) -> None:
        expect(self.verwijder_knop).to_be_visible()

    def expect_rol_waarde(self, waarde: str) -> None:
        assert self.rol_input.input_value() == waarde, (
            f"Reviewerrol niet ingevuld: {self.rol_input.input_value()!r}"
        )

    def expect_omschrijving_waarde(self, waarde: str) -> None:
        assert self.omschrijving_input.input_value() == waarde, (
            f"Omschrijving niet ingevuld: {self.omschrijving_input.input_value()!r}"
        )


class ReviewerList:
    def __init__(self, page: Page):
        self.page = page
        self.toevoegen_knop = page.get_by_test_id("reviewer-toevoegen")
        self.items = page.get_by_test_id("reviewer-item")

    # --- Actions ---
    def toevoegen(self) -> ReviewerItem:
        self.toevoegen_knop.click()
        return self.eerste()

    # --- Toegang ---
    def eerste(self) -> ReviewerItem:
        return ReviewerItem(self.items.first)

    # --- Validations ---
    def expect_toevoegen_knop_zichtbaar(self) -> None:
        expect(self.toevoegen_knop).to_be_visible()

    def expect_aantal(self, aantal: int) -> None:
        expect(self.items).to_have_count(aantal)
