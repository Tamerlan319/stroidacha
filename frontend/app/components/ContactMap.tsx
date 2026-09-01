type ContactMapProps = {
  embedUrl: string;
  linkUrl: string;
  title: string;
};

// Карта Яндекса при открытии сама показывает балун "Организации в доме" /
// "Сообщить об ошибке" — это поведение встроенного виджета Яндекса для
// геокодированного адреса, средствами iframe его не убрать (кросс-доменная
// страница, до её внутренней вёрстки нет доступа), а платный вариант без
// этого (Static Maps API) требует отдельного API-ключа и биллинга — того
// же самого, через что только что прошли с SmartCaptcha. Карта показывается
// сразу, балун — известный, но второстепенный момент на фоне остального
// оформления карточки.
export default function ContactMap({ embedUrl, linkUrl, title }: ContactMapProps) {
  if (!embedUrl) {
    return <div className="contactMapPlaceholder">Карта пока не добавлена</div>;
  }

  return (
    <>
      <iframe src={embedUrl} title={title} loading="lazy" />
      <a
        className="contactMapExternalLink"
        href={linkUrl}
        rel="noreferrer"
        target="_blank"
      >
        Открыть в Яндекс.Картах →
      </a>
    </>
  );
}
