import Link from "next/link";

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Yuz Tanish Davomat Tizimi
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Real-time yuz tanish orqali davomat olish tizimi
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          <Link href="/registration">
            <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer">
              <div className="text-4xl mb-4">👤</div>
              <h2 className="text-2xl font-semibold mb-2">Ro'yxatdan o'tish</h2>
              <p className="text-gray-600">
                Yangi talaba qo'shish va rasmlarni yuklash
              </p>
            </div>
          </Link>
          
          <Link href="/attendance">
            <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer">
              <div className="text-4xl mb-4">📸</div>
              <h2 className="text-2xl font-semibold mb-2">Davomat Olish</h2>
              <p className="text-gray-600">
                Kamera orqali real-time davomat olish
              </p>
            </div>
          </Link>
          
          <Link href="/dashboard">
            <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer">
              <div className="text-4xl mb-4">📊</div>
              <h2 className="text-2xl font-semibold mb-2">Dashboard</h2>
              <p className="text-gray-600">
                Davomat statistikasi va hisobotlar
              </p>
            </div>
          </Link>
        </div>
        
        <div className="mt-12 bg-blue-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">Tizim Xususiyatlari</h3>
          <ul className="text-left max-w-2xl mx-auto space-y-2 text-gray-700">
            <li>✓ 10,000+ talaba uchun optimallashtirilgan</li>
            <li>✓ Real-time yuz tanish (2 sekund ichida)</li>
            <li>✓ 0.6+ ishonch darajasi bilan aniq tanish</li>
            <li>✓ Bir talaba bir kun ichida bir marta davomat</li>
            <li>✓ FAISS vector database bilan tez qidiruv</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

