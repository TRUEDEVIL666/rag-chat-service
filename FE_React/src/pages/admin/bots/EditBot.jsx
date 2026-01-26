import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useBots } from '../../../hooks/useBots';
import BotForm from './BotForm';
import { SpinnerIcon } from '@phosphor-icons/react';



const EditBot = () => {
  const { id } = useParams();
  const { fetchBot } = useBots();
  const [botData, setBotData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadBot = async () => {
      try {
        const data = await fetchBot(id);

        if (data) {
          const formattedData = {
            id: data.id,
            bot_name: data.name,
            description: data.description,
            provider_id: data.provider_id,
            model_id: data.model_id,
            system_prompt: data.config_prompt,
            config_model: data.config_model
          };
          setBotData(formattedData);
        } else {
          // Handle null case if fetchBot returns null on error
          alert("Không tìm thấy Bot!");
        }
      } catch (error) {
        // fetchBot handles its own error logging, but we might want to alert
        console.error("Failed to fetch bot", error);
      } finally {
        setLoading(false);
      }
    };
    loadBot();
  }, [id, fetchBot]);

  if (loading) return <div className="flex justify-center items-center h-full"><SpinnerIcon className="animate-spin text-primary-600" size={32} /></div>;

  return <BotForm initialData={botData} isEdit={true} />;
};

export default EditBot;
