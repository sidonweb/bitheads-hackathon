import { BLOCK_REGISTRY, UnknownBlock } from './registry.js';

export default function BlockRenderer({ blocks = [], handlers = {} }) {
  if (!blocks?.length) return null;

  return (
    <div className="sdui-blocks">
      {blocks.map((block) => {
        const Component = BLOCK_REGISTRY[block.type];
        if (!Component) {
          return <UnknownBlock key={block.id || block.type} type={block.type} />;
        }
        return <Component key={block.id} {...block} handlers={handlers} />;
      })}
    </div>
  );
}

export function hasDecisionCardBlock(blocks) {
  return Array.isArray(blocks) && blocks.some((b) => b.type === 'decision_card');
}
