import { useState } from "react";
import "./Sidebar.css";

const storyCategories = {
  "Comic Stories": [
    "Tell me a story about two funny rabbits who discover a secret carrot cave",
    "Tell me a comic story about a lazy lion who hates waking up",
    "Tell me a comic story about a monkey who wants to be a king",
    "Tell me a funny story about a cat who thinks he can fly",
    "Tell me a comic story about a buffalo who joins a dance class"
  ],
  "Adventure": [
    "Tell me an adventure story about a boy who finds a talking map",
    "Tell me a story about a forest adventure with hidden treasure",
    "Tell me a story about two friends who travel in a flying boat",
    "Tell me an adventure story about a glowing mountain",
    "Tell me an adventure story about a girl searching for a golden feather"
  ],
  "Moral Stories": [
    "Tell me a moral story about honesty",
    "Tell me a moral story about helping others",
    "Tell me a moral story about sharing",
    "Tell me a moral story about respecting elders",
    "Tell me a moral story about friendship"
  ],
  "Festival Tales": [
    "Tell me a Diwali story for kids",
    "Tell me a Christmas story for kids",
    "Tell me an Eid story for kids",
    "Tell me a Sankranti story for kids",
    "Tell me a Holi story for kids"
  ],
  "Animal Stories": [
    "Tell me a story about a clever fox and a kind deer",
    "Tell me a story about a brave baby elephant",
    "Tell me a story about a parrot and a squirrel who become friends",
    "Tell me a story about a tiger who learns to share",
    "Tell me a story about a dog who becomes a hero"
  ],
  "Space / Sci-Fi": [
    "Tell me a story about two kids who visit Mars",
    "Tell me a story about a robot who wants to learn music",
    "Tell me a story about a space zoo",
    "Tell me a story about a glowing alien who needs help",
    "Tell me a story about a spaceship made of candy"
  ],
  "Magic / Fantasy": [
    "Tell me a story about a magical talking tree",
    "Tell me a story about a girl with a flying umbrella",
    "Tell me a story about a wizard and a tiny dragon",
    "Tell me a story about a magical rainbow bridge",
    "Tell me a fantasy story about a wish-granting river"
  ],
  "Bedtime Calm": [
    "Tell me a slow bedtime story with moon and stars",
    "Tell me a bedtime story about clouds and dreams",
    "Tell me a bedtime story about a sleepy panda",
    "Tell me a bedtime story about a floating island",
    "Tell me a bedtime story about a baby whale"
  ],
  "Funny Stories": [
    "Tell me a funny story about a talking potato",
    "Tell me a funny story about a dancing goat",
    "Tell me a funny story about slippers that run away",
    "Tell me a funny story about a fish who tells jokes",
    "Tell me a funny story about a penguin who hates snow"
  ],
  "Friendship": [
    "Tell me a story about four friends who save their village",
    "Tell me a story about best friends who never give up",
    "Tell me a story about two friends who build a secret clubhouse",
    "Tell me a story about friendship and trust",
    "Tell me a story about friends who learn to work together"
  ]
};

export default function Sidebar({ onSelectStory }) {
  const [openCategory, setOpenCategory] = useState(null);

  return (
    <div className="sidebar">
      <h2 className="sidebar-title">✨ Story Library</h2>

      {Object.entries(storyCategories).map(([category, stories]) => (
        <div key={category} className="category-block">
          
          <h3
            className="category-title"
            onClick={() => setOpenCategory(openCategory === category ? null : category)}
          >
            {category}
            <span className="arrow">{openCategory === category ? "▲" : "▼"}</span>
          </h3>

          {openCategory === category && (
            <ul>
              {stories.map((s, i) => (
                <li key={i} className="story-item" onClick={() => onSelectStory(s)}>
                  ✨ {s}
                </li>
              ))}
            </ul>
          )}

        </div>
      ))}
    </div>
  );
}