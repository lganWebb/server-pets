import traceback
import asyncio
import random
import json

import discord
from discord.ext import commands

class Accounts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conversion = {
            "dog food": "Dog Food",
            "cat food": "Cat Food",
            "mouse food": "Mouse Food",
            "snake food": "Snake Food",
            "spider food": "Spider Food",
            "bird food": "Bird Food",
            "horse food": "Horse Food",
            "water bowls": "Water Bowls"
        }
    
    @commands.command(name="create")
    async def create_(self, ctx):
        """Creates an account"""
        account = await self.bot.db.fetch("SELECT * FROM accounts WHERE owner_id = $1", ctx.author.id)

        if account:
            return await ctx.send("You already have an account! To view it please say `p-account`.")

        pet_bars = json.dumps({"thirst":{},"hunger":{}})
        items = json.dumps({"water bowls": 0})
        await self.bot.db.execute("INSERT INTO accounts (owner_id, balance, pet_bars, items) VALUES ($1,$2,$3,$4)", ctx.author.id, 600, pet_bars, items)
        
        return await ctx.message.add_reaction(":greenTick:596576670815879169")
    
    @commands.command(name="delete")
    async def delete_(self, ctx):
        """Deletes an account"""
        account = await self.bot.db.fetch("SELECT * FROM accounts WHERE owner_id = $1", ctx.author.id)

        if not account:
            return await ctx.send("You do not have an account!")

        confirm_embed = discord.Embed(title="Confirm", description="Are you sure?\nPlease react with <:greenTick:596576670815879169> to confirm, or <:redTick:596576672149667840> to cancel.", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
        confirm_embed.set_thumbnail(url=ctx.guild.me.avatar_url)

        bot_msg = await ctx.send(embed=confirm_embed)

        await bot_msg.add_reaction(":greenTick:596576670815879169")
        await bot_msg.add_reaction(":redTick:596576672149667840")

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=600, check=lambda r, u: u == ctx.author and str(r.emoji) in ["<:greenTick:596576670815879169>", "<:redTick:596576672149667840>"])
            if str(reaction.emoji) == "<:greenTick:596576670815879169>":
                await bot_msg.delete()
            else:
                return await ctx.send("Canceled.")
        except asyncio.TimeoutError:
            return await ctx.send("Time ran out.")

        await self.bot.db.execute("DELETE FROM accounts WHERE owner_id = $1", ctx.author.id)

        return await ctx.send("Your account has been deleted.")

    @commands.command(name="account")
    async def account_(self, ctx, user:discord.Member=None):
        """Get the account of a user or yourself."""
        user = ctx.author if user is None else user
        account = await self.bot.db.fetch("SELECT * FROM accounts WHERE owner_id = $1", user.id)

        if not account:
            return await ctx.send("The user in question does not have an account. Use `p-create` to make one.")

        embed = discord.Embed(title=f"{user.name}'s account. ({user.id})", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
        embed.set_thumbnail(url=user.avatar_url)

        if account[0]["pets"]:
            embed.add_field(name="Pets", value=", ".join(account[0]['pets']))
        else:
            embed.add_field(name="Pets", value="None")
        embed.add_field(name="Balance", value=f"${account[0]['balance']}")

        return await ctx.send(embed=embed)
    
    @commands.command(name="pets")
    async def pets_(self, ctx, user:discord.Member=None):
        """Find out the hunger and thirst of a users or your animals."""
        user = ctx.author if user is None else user

        account = await self.bot.db.fetch("SELECT * FROM accounts WHERE owner_id = $1", user.id)

        if not account:
            return await ctx.send("The user in question does not have an account.")
        
        bars = json.loads(account[0]["pet_bars"])

        embed = discord.Embed(title=f"{user.name}'s animals.", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)

        if not account[0]["pets"]:
            embed.add_field(name="This user has no pets.", value="** **")
        else: 
            for pet in account[0]["pets"]:
                val = ""

                # hunger
                try:
                    val += f"Hunger: {str(bars['hunger'][pet])[:4]}/10"
                except KeyError:
                    val += f"Hunger: 10/10"
                
                # thirst
                try:
                    val += f"\nThirst: {str(bars['thirst'][pet])[:4]}/20"
                except KeyError:
                    val += f"\nThirst: 20/20"

                embed.add_field(name=pet, value=val)
        
        embed.set_thumbnail(url=user.avatar_url)

        return await ctx.send(embed=embed)
    
    @commands.command(name="supplies")
    async def supplies_(self, ctx, user:discord.Member=None):
        """Shows the supplies of a user or yourself."""
        try:
            user = ctx.author if user is None else user
            account = await self.bot.db.fetch("SELECT * FROM accounts WHERE owner_id = $1", user.id)

            if not account:
                return await ctx.send("The user in question does not have an account.")
            
            items = json.loads(account[0]["items"])

            embed = discord.Embed(title=f"{user.name}'s supplies", colour=discord.Colour.blue(), timestamp=ctx.message.created_at
            
            for key, value in items.items():
                if key != "water bowls":
                    embed.add_field(name=self.conversion[key], value=value, inline=False)

            embed.add_field(name="Water Bowls", value=items["water bowls"], inline=False)
    
            embed.set_thumbnail(url=user.avatar_url)
            return await ctx.send(embed=embed)
        except Exception:
            traceback.print_exc()
    
    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard_(self, ctx, lb_type=None):
        """Get a leaderboard of the people in your server or globally. For server leave `lb_type` empty, for global use `p-lb global`"""
        accounts = await self.bot.db.fetch("SELECT * FROM accounts ORDER BY balance DESC LIMIT 5")
        
        if lb_type == None:
            embed = discord.Embed(title=f"{ctx.guild.name}'s leaderboard", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
            accounts = [account for account in accounts if account["owner_id"] in [member.id for member in ctx.guild.members]]
        else:
            embed = discord.Embed(title=f"Global leaderboard", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)

        index = 0
        for account in accounts:
            index += 1

            user = self.bot.get_user(account["owner_id"])
            embed.add_field(name=f"{index} | {user}", value=f"{len(account['pets']) if account['pets'] else '0'} pets, has ${account['balance']}", inline=False)
            embed.add_field(name="** **", value="** **", inline=False)
        
        if lb_type == None:
            embed.set_thumbnail(url=ctx.guild.icon_url)
        else:
            embed.set_thumbnail(url=ctx.guild.me.avatar_url)
        
        embed.set_footer(text=f"Your rank: {[account['owner_id'] for account in accounts].index(ctx.author.id)+1}")

        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Accounts(bot))