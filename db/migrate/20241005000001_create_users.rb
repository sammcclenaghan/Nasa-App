class CreateUsers < ActiveRecord::Migration[8.0]
  def change
    create_table :users do |t|
      t.string :username, null: false
      t.string :email, null: false
      t.string :first_name
      t.string :last_name
      t.string :password_digest, null: false
      
      # NASA Earthdata credentials
      t.string :earthdata_username, null: false
      t.text :earthdata_password, null: false # Will be encrypted
      
      t.boolean :admin, default: false
      t.datetime :last_login_at
      
      t.timestamps
    end
    
    add_index :users, :username, unique: true
    add_index :users, :email, unique: true
    add_index :users, :earthdata_username
  end
end