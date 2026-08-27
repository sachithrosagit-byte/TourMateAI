// Compact attraction card rendered inline under an assistant reply — thumbnail,
// name, category + rating. Links to the attraction's detail page.

import { Link } from 'react-router-dom'
import AttractionImage from '../explore/AttractionImage'

export default function ChatSuggestionCard({ attraction }) {
  return (
    <Link to={`/explore/${attraction.id}`} className="chat-suggestion">
      <div className="chat-suggestion-thumb">
        <AttractionImage attraction={attraction} className="chat-suggestion-img" />
      </div>
      <div className="chat-suggestion-body">
        <span className="chat-suggestion-name">{attraction.name}</span>
        <span className="chat-suggestion-meta">
          {attraction.category}
          {attraction.avg_rating ? (
            <>
              <span aria-hidden="true"> · </span>
              <span className="chat-suggestion-rating">
                ★ {attraction.avg_rating.toFixed(1)}
              </span>
            </>
          ) : null}
        </span>
      </div>
      <svg
        className="chat-suggestion-arrow"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="m9 6 6 6-6 6"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </Link>
  )
}
