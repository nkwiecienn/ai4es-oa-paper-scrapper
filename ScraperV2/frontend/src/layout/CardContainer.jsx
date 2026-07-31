function CardContainer({ children, className = "" }) {
    return (
        <div
            className={`relative flex h-full w-full max-w-5xl flex-col overflow-hidden rounded-b-3xl rounded-t-none bg-surface_container px-5 py-6 text-on-surface sm:px-8 sm:py-8 ${className}`}
        >
            {children}
        </div>
    );
}

export default CardContainer;