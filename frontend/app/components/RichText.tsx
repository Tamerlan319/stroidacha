type RichTextProps = {
  value: string;
  className?: string;
};

function paragraphContent(value: string) {
  const match = value.match(/^([^:]{2,70}:)\s+([\s\S]+)$/);
  if (!match) return value;

  return (
    <>
      <strong>{match[1]}</strong> {match[2]}
    </>
  );
}

export default function RichText({ value, className = "" }: RichTextProps) {
  const blocks = value
    .replace(/\r\n/g, "\n")
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  return (
    <div className={`richText ${className}`.trim()}>
      {blocks.map((block, index) => {
        if (block.startsWith("### ")) {
          return <h3 key={index}>{block.slice(4)}</h3>;
        }
        if (block.startsWith("## ")) {
          return <h2 key={index}>{block.slice(3)}</h2>;
        }
        if (block.startsWith("- ")) {
          return (
            <ul key={index}>
              {block.split("\n").map((item, itemIndex) => (
                <li key={itemIndex}>{paragraphContent(item.replace(/^-\s*/, ""))}</li>
              ))}
            </ul>
          );
        }

        return <p key={index}>{paragraphContent(block)}</p>;
      })}
    </div>
  );
}
