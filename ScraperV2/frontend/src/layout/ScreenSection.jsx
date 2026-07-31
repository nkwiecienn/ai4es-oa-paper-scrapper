import {
    screenSectionClassName,
    screenSectionContentClassName,
    screenSectionHeaderClassName,
    screenSectionInnerClassName,
    screenSectionSubtitleClassName,
    screenSectionTitleClassName,
    screenSectionTitleGlowClassName,
} from '../styles/layoutClasses';

function ScreenSection({ id, heading, subheading, children }) {
    return (
        <section id={id} className={screenSectionClassName}>
            <div className={screenSectionInnerClassName}>
                <header className={screenSectionHeaderClassName}>
                    <h1 className={screenSectionTitleClassName}>
                        <span
                            aria-hidden="true"
                            className={screenSectionTitleGlowClassName}
                        />
                        <span className="relative">
                            {heading}
                        </span>
                    </h1>
                    <p className={screenSectionSubtitleClassName}>
                        {subheading}
                    </p>
                </header>

                <div className={screenSectionContentClassName}>
                    {children}
                </div>
            </div>
        </section>
    );
}

export default ScreenSection;