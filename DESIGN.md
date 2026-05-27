# 🐱 Zeno AutoClicker - Design System

## Conceito Visual
**Tema:** Gatos Pretos & Tecnologia Sombria  
**Vibe:** Mystério, elegância felina, power oculto  
**Produto:** Auto-clicker premium para Minecraft - **$5 USD**

---

## Paleta de Cores

### Principais
- **Preto Profundo:** `#0a0a0a` - Background principal
- **Cinza Escuro:** `#141414` - Cards e sections
- **Cinza Médio:** `#1e1e1e` - Borders e divisores

### Accent (Gato Preto)
- **Roxo Místico:** `#8b5cf6` - Primary accent (olhos de gato)
- **Roxo Escuro:** `#6d28d9` - Hover states
- **Roxo Neon:** `#a78bfa` - Glow effects

### Secundárias
- **Verde Neon:** `#10b981` - Success, disponível
- **Amarelo Ouro:** `#fbbf24` - Premium badge
- **Vermelho:** `#ef4444` - Alertas (manter do original se necessário)

### Texto
- **Branco Puro:** `#ffffff` - Headings
- **Cinza Claro:** `#e5e5e5` - Body text
- **Cinza Médio:** `#a3a3a3` - Subtexts
- **Cinza Escuro:** `#525252` - Disabled/muted

---

## Tipografia

### Fontes
```css
--font-display: 'Space Grotesk', 'Segoe UI', system-ui, sans-serif;
--font-body: 'Inter', 'Segoe UI', system-ui, sans-serif;
```

### Tamanhos
- **Hero Title:** 64-80px (bold 800)
- **Section Title:** 36-48px (bold 700)
- **Card Title:** 20-24px (semibold 600)
- **Body:** 16-18px (regular 400)
- **Caption:** 12-14px (medium 500)

---

## Elementos Visuais

### Gatos Pretos
- **Hero Section:** Silhueta de gato preto no canto com olhos brilhando (roxo neon)
- **Background Pattern:** Pegadas de gato sutis em parallax
- **Cursor Hover:** Trilha de pegadas ao mover mouse (opcional)
- **Loading:** Gato preto andando/cauda balançando

### Animações
- **Entrada:** Fade in + slide up (stagger nos cards)
- **Hover Cards:** Lift (translateY -8px) + glow roxo
- **Botões:** Scale (1.05) + pulse no border
- **Background:** Partículas flutuantes roxas (estrelas/poeira)
- **Gato Hero:** Piscar olhos a cada 3-5s
- **Scroll:** Parallax nas pegadas de fundo

### Ícones & Ilustrações
- Silhuetas de gatos em poses dinâmicas
- Pegadas espalhadas decorativamente
- Olhos brilhando no dark mode
- Mouse cursor com pegada de gato (opcional)

---

## Estrutura das Páginas

### 1. Landing Page (index.html)
**Seções:**
1. **Hero:**
   - Logo Zeno + silhueta gato preto
   - Título: "Domine o Minecraft com Zeno"
   - Subtítulo: "O auto-clicker mais elegante e poderoso"
   - Badge: "Premium - $5 USD"
   - CTA: "Comprar Agora" → Kiwify checkout
   
2. **Features:**
   - Grid 3 colunas com ícones
   - Jitter click, Sons, Hotkeys, Tray, Themes
   - Animação stagger no scroll
   
3. **Showcase:**
   - Screenshot ou mockup do app
   - Gatos decorativos ao redor
   
4. **Pricing:**
   - Card único centralizado
   - $5 USD - Acesso vitalício
   - Lista de features incluídas
   - CTA: "Garantir Meu Zeno"
   
5. **Footer:**
   - Links sociais/suporte
   - Copyright
   - Pegadas de gato no rodapé

### 2. Página de Pagamento (payment.html)
**Estrutura:**
- Layout limpo e focado
- Logo + breadcrumb (Home > Checkout)
- Card de resumo do produto:
  - Zeno AutoClicker
  - $5 USD
  - Features incluídas
- Integração Kiwify (embed ou redirect)
- Garantia/Trust badges
- Footer minimalista

---

## Componentes

### Botão Primary
```css
background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
border-radius: 12px;
padding: 14px 32px;
font-weight: 700;
box-shadow: 0 0 30px rgba(139, 92, 246, 0.4);
transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 0 40px rgba(139, 92, 246, 0.6);
}
```

### Card
```css
background: rgba(20, 20, 20, 0.6);
backdrop-filter: blur(20px);
border: 1px solid rgba(139, 92, 246, 0.2);
border-radius: 16px;
padding: 24px;
transition: all 0.3s ease;

:hover {
  transform: translateY(-8px);
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 20px 60px rgba(139, 92, 246, 0.3);
}
```

### Badge Premium
```css
background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
color: #0a0a0a;
border-radius: 20px;
padding: 6px 16px;
font-size: 12px;
font-weight: 700;
text-transform: uppercase;
letter-spacing: 1px;
```

---

## Interações

### Micro-animações
- **Botão CTA:** Pulse contínuo sutil no glow
- **Preço:** Counter animado de 0 → $5
- **Features:** Check marks aparecem em sequência
- **Gato Hero:** Cauda balança levemente (CSS animation)

### Hover States
- Cards elevam e brilham
- Botões crescem e pulsam
- Links mudam cor + underline slide
- Imagens fazem zoom suave

### Loading States
- Skeleton screens com gradiente
- Spinner com pegada de gato rotacionando
- Progress bar roxo neon

---

## Responsividade

### Breakpoints
- **Mobile:** < 640px
- **Tablet:** 640px - 1024px
- **Desktop:** > 1024px

### Ajustes Mobile
- Hero title: 36-42px
- Grid features: 1 coluna
- Padding reduzido
- Gato hero simplificado (só olhos)
- Bottom sheet para checkout (mobile-first)

---

## Implementação Kiwify

### Landing → Checkout
```html
<!-- Botão CTA primário -->
<a href="payment.html" class="btn-primary">
  Comprar Agora - $5
</a>
```

### Payment Page
```html
<!-- Embed Kiwify checkout -->
<div id="kiwify-checkout">
  <!-- Código de integração Kiwify aqui -->
  <!-- Usuário fornecerá o link/código do produto -->
</div>
```

**Nota:** Solicitar ao usuário:
- Link do produto Kiwify
- Preferência: embed direto ou redirect
- Pixel de conversão (se houver)

---

## Assets Necessários

### Imagens
- ✅ logo.png (já existe)
- ✅ logo.ico (já existe)
- 🆕 cat-silhouette.svg (silhueta gato preto)
- 🆕 cat-eyes.svg (olhos brilhando)
- 🆕 paw-prints.svg (pegadas decorativas)
- 🆕 app-screenshot.png (opcional - mockup do Zeno)

### Fontes
- Space Grotesk (Google Fonts)
- Inter (Google Fonts)

### Animações
- Particles.js ou custom CSS animations
- Lottie (opcional - gato animado)

---

## Notas de Desenvolvimento

### Performance
- Lazy load imagens
- Minify CSS/JS
- Optimize SVGs
- Preload fonts críticas

### SEO
- Meta tags para $5 product
- Open Graph (imagem com gato)
- Schema.org Product markup
- Alt texts descritivos

### Acessibilidade
- Contraste WCAG AA mínimo
- Focus states visíveis
- ARIA labels
- Keyboard navigation

---

## Inspirações

- **Aesthetic:** Cyberpunk + Mystical + Feline elegance
- **Referencias:** Discord Nitro, Spotify Premium, produtos tech de nicho
- **Mood:** "Se Batman tivesse um auto-clicker, seria o Zeno" 🦇🐱

---

**Versão:** 1.0  
**Data:** Maio 2026  
**Status:** Ready para implementação 🚀
