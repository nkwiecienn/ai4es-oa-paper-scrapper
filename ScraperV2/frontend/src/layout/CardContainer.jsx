import { cardContainerClassName } from '../styles/layoutClasses';

function CardContainer({ children, className = "" }) {
    return (
        <div
            className={`${cardContainerClassName} ${className}`}
        >
            {children}
        </div>
    );
}

export default CardContainer;