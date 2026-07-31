function ScreenSection({ id, heading, subheading, children }) {
    return (
        <section id={id} className="flex min-h-screen snap-start items-center bg-gradient-to-b from-surface_container via-surface_container to-background px-4 py-6 sm:px-6 lg:px-8">
            <div className="mx-auto flex w-full max-w-6xl flex-col items-center gap-5 text-center">
                <header className="space-y-2">
                    <h1 className="text-4xl font-extrabold tracking-tight text-primary sm:text-5xl md:text-6xl">
                        {heading}
                    </h1>
                    <p className="mx-auto max-w-3xl text-sm text-on-surface-variant sm:text-base md:text-lg">
                        {subheading}
                    </p>
                </header>

                <div className="flex w-full min-h-0 flex-1 items-center justify-center">
                    {children}
                </div>
            </div>
        </section>
    );
}

export default ScreenSection;