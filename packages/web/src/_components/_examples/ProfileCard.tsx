import React from "react";

const ProfileCard: React.FC<{ name: string; role: string; imageUrl: string; bio: string }> = ({
  name,
  role,
  imageUrl,
  bio,
}) => {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300">
      <img src={imageUrl} alt={name} className="w-full h-48 object-cover" />
      <div className="p-4">
        <h3 className="text-2xl font-bold mb-1">{name}</h3>
        <p className="text-green-500 font-medium mb-2">{role}</p>
        <p className="text-gray-600">{bio}</p>
      </div>
    </div>
  );
};

export default ProfileCard;
