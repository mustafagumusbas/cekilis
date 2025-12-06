import discord
from discord.ext import commands, tasks
from logic import DatabaseManager, hide_img
from config import TOKEN, DATABASE

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

manager = DatabaseManager(DATABASE)
manager.create_tables()

@bot.command()
async def start(ctx):
    user_id = ctx.author.id
    if user_id in manager.get_users():
        await ctx.send("Zaten kayıtlısınız!")
    else:
        manager.add_user(user_id, ctx.author.name)
        await ctx.send("Kaydoldunuz! Resimler düzenli olarak gönderilecek.")

@bot.command()
async def rating(ctx):
    users = manager.get_rating()  
    text = "```\nKullanıcı        Puan\n----------------------\n"
    for name, score in users:
        text += f"{name:<15} {score}\n"
    text += "```"
    await ctx.send(text)

@tasks.loop(minutes=1)
async def send_message():
    for user_id in manager.get_users():
        prize_id, img = manager.get_random_prize()[:2]
        hide_img(img)
        user = await bot.fetch_user(user_id)
        if user:
            await send_image(user, f'hidden_img/{img}', prize_id)
        manager.mark_prize_used(prize_id)

async def send_image(user, image_path, prize_id):
    file = discord.File(image_path)
    button = discord.ui.Button(label="Al!", custom_id=str(prize_id))
    view = discord.ui.View()
    view.add_item(button)
    await user.send(file=file, view=view)

@bot.event
async def on_interaction(interaction):
    if interaction.type != discord.InteractionType.component:
        return

    prize_id = interaction.data["custom_id"]
    user_id = interaction.user.id

    if manager.get_winner_count(prize_id) >= 3:
        await interaction.response.send_message(
            "Bu ödül zaten dağıtıldı.", ephemeral=True
        )
        return

    if manager.add_winner(user_id, prize_id):
        img = manager.get_prize_img(prize_id)
        file = discord.File(f"img/{img}")
        await interaction.response.send_message(
            content="Tebrikler, resmi aldınız!", file=file
        )
    else:
        await interaction.response.send_message(
            "Bu resmi zaten aldınız.", ephemeral=True
        )

@bot.event
async def on_ready():
    print(f'{bot.user} giriş yaptı')
    if not send_message.is_running():
        send_message.start()

bot.run(TOKEN)
