import ProjectDescription from "./components/ProjectDescription";
import CardContainer from "./layout/CardContainer";
import PaperExtractionStepper from "./layout/Stepper";
import ScreenSection from "./layout/ScreenSection";

function App() {
  return (
    <div className="h-screen overflow-y-scroll snap-y snap-mandatory scroll-smooth">
      <ScreenSection
        heading="Project Overview"
        subheading="Scraping Open-Access Research Papers"
      >
        <CardContainer>
          <ProjectDescription />
        </CardContainer>
      </ScreenSection>

      <ScreenSection
        heading="Search papers"
        subheading="Search for papers with keywords, then select papers to extract."
      >
        <CardContainer>
          Page 2
        </CardContainer>
      </ScreenSection>


      <ScreenSection
        id="data-extraction"
        heading="Data Extraction"
        subheading="Parse papers to extract sections, tables, and metadata into clean structured outputs."
      >
        <CardContainer>
          <PaperExtractionStepper />
        </CardContainer>
      </ScreenSection>
    </div>
  );
}

export default App;