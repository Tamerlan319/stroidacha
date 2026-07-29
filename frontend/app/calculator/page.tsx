import type { Metadata } from "next";

import HouseCalculator from "../components/HouseCalculator";
import LeadForm from "../components/LeadForm";

export const metadata: Metadata = {
  title: "Калькулятор стоимости дома из бруса",
  description:
    "Предварительный расчёт стоимости дома из бруса по площади, этажности, материалу, фундаменту и кровле на основе цен реальных проектов.",
};

export default function CalculatorPage() {
  return (
    <main>
      <section className="calculatorHero">
        <div className="container calculatorHeroInner">
          <div>
            <p className="heroKicker">Калькулятор строительства</p>
            <h1>Рассчитайте примерную стоимость своего дома</h1>
            <p className="heroText">
              Укажите площадь, этажность и материал. Расчёт сравнит параметры с
              реальными проектами каталога и покажет ориентировочный диапазон цены.
            </p>
          </div>

          <div className="calculatorHeroNote">
            <span>Сейчас считаем</span>
            <strong>Дома из бруса</strong>
            <p>Базовая комплектация «под усадку», фундамент и кровля — отдельно.</p>
          </div>
        </div>
      </section>

      <section className="container calculatorSection">
        <HouseCalculator />
      </section>

      <section className="container section" id="calculator-lead">
        <div className="calculatorLeadGrid">
          <div>
            <p className="eyebrow">Точный расчёт</p>
            <h2>Нужна смета под ваш проект?</h2>
            <p>
              Калькулятор даёт ориентир. Для точной цены менеджер проверит планировку,
              фундамент, кровлю, участок и состав работ.
            </p>
          </div>
          <LeadForm source="calculator" title="Получить точную смету" />
        </div>
      </section>
    </main>
  );
}
