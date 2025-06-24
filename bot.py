import disnake
from disnake import ui, SelectOption
from disnake.ui import ActionRow
from disnake.ui import View, Button, ActionRow, Select, TextInput
from disnake import ButtonStyle, Button
from disnake.ext import commands
from api import add_player_to_whitelist
from beammp import check_beammp_player
import sqlite3


discord_token = ""
db = sqlite3.connect('suspicious_accounts.db')
cursor = db.cursor()
db.execute('''CREATE TABLE IF NOT EXISTS suspicious_accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT,discord_name TEXT,account_age INTEGER,beammp_name TEXT,character_name TEXT,registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

intents = disnake.Intents.default()
intents.typing = False
intents.presences = False
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
            
@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")
    channel_pass = bot.get_channel(1342208326896980079) # id канала, где будет кнопка.
    existing_message_pass = None 
    async for message in channel_pass.history(limit=10): 
        if message.author == bot.user: 
            existing_message_pass = message 
            break 
 
    if existing_message_pass is not None: 
        await existing_message_pass.delete()

    embed = disnake.Embed(
        title="🎮 Регистрация на сервере MaxiTown",
        description="Для начала игры необходимо пройти регистрацию",
        color=disnake.Color.blue()
    )
    embed.add_field(
        name="📚 Важная информация",
        value="Смотрите канал https://discord.com/channels/1341469479510474813/1341836516527312977\n"
              "Там вы найдете подробную инструкцию в разделе **'Как начать играть'**",
        inline=False
    )
    embed.add_field(
        name="⬇️ Регистрация",
        value="Нажмите на кнопку ниже, чтобы начать процесс регистрации",
        inline=False
    )
    embed.set_footer(text="MaxiTown - Система регистрации")
    
    await channel_pass.send(embed=embed, view=PerpetualView())


class MyModal(disnake.ui.Modal):
    def __init__(self):
        super().__init__(title="Регистрация", components=[
            disnake.ui.TextInput(label="Имя и фамилия вашего персонажа:", placeholder="Пример: Генадий Карамыслов",min_length=6, max_length=16, custom_id="username"), 
            disnake.ui.TextInput(label="Ваш никнейм BeamMP https://forum.beammp.com/", placeholder="Пример: pirojok",min_length=3, max_length=16, custom_id="beammp"),])

    async def callback(self, interaction: disnake.ModalInteraction):  

        await interaction.response.defer(ephemeral=True)
        
        traceback_channel = disnake.utils.get(interaction.guild.channels, id=1341474910710534198) # ID Канала для отправки уведомления админам о регистрации.
        name = interaction.text_values.get("username")
        beammp = interaction.text_values.get("beammp")
        

        account_age = (interaction.created_at - interaction.user.created_at).days
        if account_age < 180:  
                db.execute('''
                    INSERT INTO suspicious_accounts (user_id, discord_name, account_age, beammp_name, character_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (interaction.user.id, str(interaction.user), account_age, beammp, name))
                
                db.commit()
                cursor.execute("SELECT last_insert_rowid()")
                ids = cursor.fetchone()[0]

                embed = disnake.Embed(
                    title="⚠️ Новая заявка на регистрацию",
                    description="Требуется проверка нового аккаунта",
                    color=disnake.Color.yellow()
                )
                embed.add_field(
                    name="📝 Информация о заявке",
                    value=f"**ID заявки:** {ids}\n"
                          f"**Пользователь:** {interaction.user.mention}\n"
                          f"**Возраст аккаунта:** {account_age} дней\n"
                          f"**BeamMP:** {beammp}\n"
                          f"**Имя персонажа:** {name}",
                    inline=False
                )
                embed.add_field(
                    name="🔧 Действия",
                    value="Используйте команды:\n"
                          f"`!одобрить {ids}` - для принятия заявки\n"
                          f"`!отклонить {ids} [причина]` - для отклонения",
                    inline=False
                )
                embed.set_footer(text="MaxiTown - Система регистрации")
                
                await traceback_channel.send(
                    content="<@&1343543809367347210> <@&1342208904850964613>",  # Mention moderator roles
                    embed=embed
                )
                embed = disnake.Embed(
                    title="⚠️ Дополнительная проверка",
                    description="Ваш профиль требует дополнительной проверки для участия в проекте.",
                    color=disnake.Color.yellow()
                )
                embed.add_field(
                    name="⏳ Что дальше?",
                    value="Пожалуйста, ожидайте. Администрация рассмотрит вашу заявку в ближайшее время.",
                    inline=False
                )
                embed.set_footer(text="MaxiTown - Система регистрации")
                await interaction.edit_original_response(embed=embed)
                return
            

        try:
            first_name, last_name = name.split()
            formatted_name = f"{first_name[0].upper()}{first_name[1:].lower()} {last_name[0].upper()}{last_name[1:].lower()}"
            nick = f"{formatted_name}[{beammp}]"
        except ValueError:
            embed = disnake.Embed(
                title="❌ Ошибка регистрации", 
                description="Введите имя и фамилию через пробел!",
                color=disnake.Color.red()
            )
            await interaction.edit_original_response(embed=embed)
            return
        

        if len(nick) > 32:
            embed = disnake.Embed(
                title="❌ Ошибка регистрации",
                description="Недопустимый размер никнейма!",
                color=disnake.Color.red()
            )
            embed.add_field(
                name="📝 Что делать?",
                value="Пожалуйста, сократите ваше ролевое имя и фамилию",
                inline=False
            )
            embed.set_footer(text="MaxiTown - Система регистрации")
            await interaction.edit_original_response(embed=embed)
            return
            
        beammp_exists = check_beammp_player(beammp)
        if not beammp_exists:
            embed = disnake.Embed(
                title="❌ Ошибка регистрации",
                description="Указанный никнейм BeamMP не найден!",
                color=disnake.Color.red()
            )
            embed.add_field(
                name="📝 Что делать?",
                value="Пожалуйста, проверьте правильность написания вашего никнейма BeamMP",
                inline=False
            )
            embed.set_footer(text="MaxiTown - Система регистрации")
            await interaction.edit_original_response(embed=embed)
            return
            
        discord_id = interaction.user.id  
        

        success = add_player_to_whitelist(beammp)
        
        if success:

            citizen_role = disnake.utils.get(interaction.guild.roles, name="Гражданин")
            bez_role = disnake.utils.get(interaction.guild.roles, name="Регистрация")
            
            try:
                await interaction.user.edit(nick=nick)
                
                if citizen_role:
                    await interaction.user.add_roles(citizen_role)
                
                if bez_role:
                    await interaction.user.remove_roles(bez_role)
                
                embed = disnake.Embed(
                    title="✅ Регистрация успешна!",
                    description="Вы успешно зарегистрированы на сервере MaxiTown!",
                    color=disnake.Color.green()
                )
                embed.add_field(
                    name="🌟 Добро пожаловать!", 
                    value="Теперь вы можете полноценно участвовать в жизни сервера",
                    inline=False
                )
                embed.add_field(
                    name="🌟 Ссылка на сервер", 
                    value="[Перейти на MaxiTown](https://discord.gg/2w5EhFgqHz)",
                    inline=False
                )
                embed.set_footer(text="MaxiTown - Ваш новый дом!")
                

                try:
                    await interaction.user.send(embed=embed)
                    await interaction.edit_original_response(content="✅ Проверьте личные сообщения!")
                except disnake.Forbidden:
                    await interaction.edit_original_response(content="❌ Не удалось отправить сообщение. Пожалуйста, разрешите личные сообщения от участников сервера.")
                await traceback_channel.send(f"Автоматическая регистрация пользователя {interaction.user.mention} успешно завершена.")
            except Exception as e:
                await traceback_channel.send(f"Ошибка при регистрации пользователя {interaction.user.mention}: {str(e)}")
                await interaction.edit_original_response(content="Произошла ошибка при регистрации. Пожалуйста, обратитесь к администрации.")
        else:
            embed = disnake.Embed(
                title="❌ Ошибка регистрации",
                description="Не удалось добавить вас в вайтлист.",
                color=disnake.Color.red()
            )
            embed.add_field(
                name="📝 Что делать?",
                value="Пожалуйста, обратитесь к администрации сервера для решения проблемы",
                inline=False
            )
            embed.set_footer(text="MaxiTown - Система регистрации")
            await interaction.edit_original_response(embed=embed)

class PerpetualView(disnake.ui.View): 
    def __init__(self):
        super().__init__(timeout=None)
    @disnake.ui.button(label="Регистрация", style=disnake.ButtonStyle.primary, custom_id="register")
    async def open_modal(self, button, interaction: disnake.MessageInteraction):
        modal = MyModal()
        await interaction.response.send_modal(modal=modal)


@bot.command()
async def одобрить(ctx, registration_id: int):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
        return

    cursor.execute("SELECT * FROM suspicious_accounts WHERE id = ?", (registration_id,))
    registration = cursor.fetchone()
    
    if not registration:
        await ctx.send("Заявка с указанным ID не найдена.", ephemeral=True)
        return
        
    user_id, discord_name, account_age, beammp_name, character_name = registration[1:6]
    user = ctx.guild.get_member(user_id)
    
    if not user:
        await ctx.send("Пользователь не найден на сервере.", ephemeral=True)
        return
        

    success = add_player_to_whitelist(beammp_name)
    if success:
        nick = f"{character_name}[{beammp_name}]"
        citizen_role = disnake.utils.get(ctx.guild.roles, name="Гражданин")
        bez_role = disnake.utils.get(ctx.guild.roles, name="Регистрация")
        
        try:
            await user.edit(nick=nick)
            if citizen_role:
                await user.add_roles(citizen_role)
            if bez_role:
                await user.remove_roles(bez_role)
                
            cursor.execute("DELETE FROM suspicious_accounts WHERE id = ?", (registration_id,))
            db.commit()
            
            embed = disnake.Embed(
                title="✅ Регистрация одобрена",
                description="Ваша регистрация была одобрена модераторами!",
                color=disnake.Color.green()
            )
            try:
                await user.send(embed=embed)
            except:
                pass
                
            await ctx.send(f"Заявка {registration_id} успешно одобрена.")
            
        except Exception as e:
            await ctx.send(f"Ошибка при одобрении: {str(e)}")
    else:
        await ctx.send("Не удалось добавить пользователя в вайтлист.")

@bot.command()
async def отклонить(ctx, registration_id: int, *, reason: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("У вас нет прав для использования этой команды.")
        return


    cursor.execute("SELECT * FROM suspicious_accounts WHERE id = ?", (registration_id,))
    registration = cursor.fetchone()
    
    if not registration:
        await ctx.send("Заявка с указанным ID не найдена.")
        return
        
    user_id = registration[1]
    user = ctx.guild.get_member(user_id)
    

    cursor.execute("DELETE FROM suspicious_accounts WHERE id = ?", (registration_id,))
    db.commit()

    if user:
        embed = disnake.Embed(
            title="❌ Регистрация отклонена",
            description=f"Ваша регистрация была отклонена.\nПричина: {reason}",
            color=disnake.Color.red()
        )
        try:
            await user.send(embed=embed)
        except:
            pass
            
    await ctx.send(f"Заявка {registration_id} успешно отклонена.")
    

bot.run(discord_token)